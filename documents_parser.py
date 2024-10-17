import os
import json
import csv
from anthropic import Anthropic
from PIL import Image
import base64
import io
from pdf2image import convert_from_path
import argparse
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init()

# Initialize Anthropic client
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
client = Anthropic(api_key=anthropic_api_key)

def encode_image(image):
    """
    Encode an image to base64 string.
    
    Args:
        image (PIL.Image): The image to encode.
    
    Returns:
        str: Base64 encoded string of the image.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_data_from_image(image):
    """
    Extract data from an image using Anthropic's API.
    
    Args:
        image (PIL.Image): The image to extract data from.
    
    Returns:
        dict: Extracted data in JSON format.
    """
    base64_image = encode_image(image)
    
    prompt = """
    Extract the following fields from this ID or passport image and return them in JSON format:
    {
      "documentType": "Type of document (e.g., Passport, ID card)",
      "country": "Issuing country",
      "passportNumber": "Document number",
      "surname": "Last name",
      "givenName": "First name",
      "dateOfBirth": "Date of birth (DD/MM/YYYY)",
      "gender": "Gender (M/F)",
      "placeOfBirth": "Place of birth",
      "placeOfIssue": "Place where the document was issued",
      "dateOfIssue": "Date when the document was issued (DD/MM/YYYY)",
      "dateOfExpiry": "Expiration date of the document (DD/MM/YYYY)"
    }
    If a field is not present in the image, use null for its value.
    Just return the JSON, no other text or characters.
    """
    
    try:
        # Send request to Anthropic API
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        # Extract JSON from the response
        content = response.content
        print(f"API Response type: {type(content)}")
        print(f"API Response content: {content}")
        
        # Handle potential list response
        if isinstance(content, list) and len(content) > 0 and hasattr(content[0], 'text'):
            content = content[0].text
        
        try:
            # First, try to parse the entire content as JSON
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}JSONDecodeError: {str(e)}{Style.RESET_ALL}")
            # If that fails, try to extract JSON from the text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"{Fore.RED}Error parsing extracted JSON: {str(e)}{Style.RESET_ALL}")
                    print(f"{Fore.RED}Extracted JSON string: {json_str}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}No JSON object found in the response{Style.RESET_ALL}")
            
            # If all parsing attempts fail, return the raw content
            return {"error": "Unable to parse response", "raw_content": content}
    except Exception as e:
        print(f"{Fore.RED}Error calling Anthropic API: {str(e)}{Style.RESET_ALL}")
        return {"error": "API call failed", "details": str(e)}

def resize_and_compress_image(image, max_size=(2000, 2000), quality=85, max_bytes=5*1024*1024):
    """
    Resize the image if it exceeds the maximum size and compress it to stay under max_bytes.
    
    Args:
        image (PIL.Image): The image to resize and compress.
        max_size (tuple): The maximum (width, height) allowed.
        quality (int): Initial JPEG quality for compression (0-95).
        max_bytes (int): Maximum allowed size in bytes.
    
    Returns:
        PIL.Image: The resized and compressed image.
    """
    # Resize image if needed
    image.thumbnail(max_size, Image.LANCZOS)
    
    # Convert RGBA to RGB if necessary
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Compress image
    buffer = io.BytesIO()
    while quality > 5:  # Set a lower bound for quality to avoid infinite loop
        buffer.seek(0)
        buffer.truncate(0)
        image.save(buffer, format="JPEG", quality=quality)
        if buffer.tell() <= max_bytes:
            print(f"Image compressed to {buffer.tell()} bytes with quality {quality}")
            buffer.seek(0)
            return Image.open(buffer)
        quality -= 5
    
    raise ValueError("Unable to compress image to under 5MB while maintaining acceptable quality")

def process_file(file_path):
    """
    Process a single file (image or PDF) and extract data.
    
    Args:
        file_path (str): Path to the file to process.
    
    Returns:
        dict: Extracted data from the file.
    
    Raises:
        ValueError: If the file type is not supported or if compression fails.
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.png', '.jpg', '.jpeg', '.webp']:
        with Image.open(file_path) as img:
            img = resize_and_compress_image(img)
            return extract_data_from_image(img)
    elif file_extension == '.pdf':
        # Convert first page of PDF to image
        images = convert_from_path(file_path, first_page=1, last_page=1)
        if images:
            img = resize_and_compress_image(images[0])
            return extract_data_from_image(img)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def process_folder(folder_path, output_file):
    """
    Process all supported files in a folder and save results iteratively.
    
    Args:
        folder_path (str): Path to the folder containing files to process.
        output_file (str): Path to the output CSV file.
    
    Returns:
        list: List of dictionaries containing extracted data from each file.
    """
    data = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.pdf')):
            try:
                extracted_data = process_file(file_path)
                extracted_data['filename'] = filename
                data.append(extracted_data)
                print(f"Processed {filename}")
                
                # Save data after each file is processed
                save_to_csv(data, output_file)
                print(f"Updated results saved to {output_file}")
            except Exception as e:
                print(f"{Fore.RED}Error processing {filename}: {str(e)}{Style.RESET_ALL}")
    return data

def save_to_csv(data, output_file):
    """
    Save extracted data to a CSV file.
    
    Args:
        data (list): List of dictionaries containing extracted data.
        output_file (str): Path to the output CSV file.
    """
    if not data:
        print(f"{Fore.YELLOW}No data to save.{Style.RESET_ALL}")
        return
    
    keys = set().union(*(d.keys() for d in data))
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=sorted(keys))
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Process images and save extracted data to CSV.")
    parser.add_argument("--input", required=True, help="Path to the input folder containing images")
    parser.add_argument("--output", required=True, help="Path to the output CSV file")
    
    args = parser.parse_args()

    folder_path = args.input
    output_file = args.output
    
    # Validate input folder
    if not os.path.isdir(folder_path):
        print(f"{Fore.RED}Error: The specified input folder does not exist.{Style.RESET_ALL}")
        folder_path = input("Please enter a valid input folder path: ")
        while not os.path.isdir(folder_path):
            print(f"{Fore.RED}Error: The specified path is not a valid directory.{Style.RESET_ALL}")
            folder_path = input("Please enter a valid input folder path: ")

    # Validate output file
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.isdir(output_dir):
        print(f"{Fore.RED}Error: The directory for the output file does not exist.{Style.RESET_ALL}")
        output_file = input("Please enter a valid output file path: ")
        while not os.path.isdir(os.path.dirname(output_file)):
            print(f"{Fore.RED}Error: The specified directory for the output file is not valid.{Style.RESET_ALL}")
            output_file = input("Please enter a valid output file path: ")

    # Process the folder and save the results
    extracted_data = process_folder(folder_path, output_file)
    print(f"Final data saved to {output_file}")
