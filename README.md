![AI ixigo Logo](static/ai-ixigo-logo.png)

# AI Claude Document Parser

## Overview

AI Claude Document Parser is an intelligent tool designed to extract information from various types of identification documents, such as passports and ID cards. Using advanced image processing and AI-powered text recognition, this tool can parse important details from document images and compile them into a structured format.

Intellectual Authors: Dawar Ali & Ernesto Cohnen

For more information, visit [ixigo.tech](https://ixigo.tech)

## Features

- Supports multiple image formats (PNG, JPG, JPEG, WebP) and PDF files
- Extracts key information such as document type, personal details, and issuance information
- Utilizes Anthropic's Claude AI for accurate data extraction
- Processes entire folders of documents in batch
- Outputs results in CSV format for easy analysis and integration
- Implements image resizing and compression to optimize API usage

## Workflow

``` mermaid
graph TD
A[Input: Image/PDF] --> B[Resize & Compress]
B --> C[Encode to Base64]
C --> D[Send to Claude AI]
D --> E[Parse JSON Response]
E --> F[Save to CSV]
G[Process Next File] --> B
F --> G
 ```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/ixigo/document-parser.git
   cd document-parser
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key as an environment variable:
   ```
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

## Usage

Run the script with the required input and output parameters:

```
python documents_parser.py --input /path/to/your/images --output /path/to/your/output.csv
```

The `--input` parameter specifies the folder containing the images to process, and the `--output` parameter specifies the path for the CSV output file.

## Sample Output

The script generates a CSV file with extracted information. Here's an example of what the output might look like:
 ```
| filename | documentType | country | passportNumber | surname | givenName | dateOfBirth | gender | placeOfBirth | placeOfIssue | dateOfIssue | dateOfExpiry |
|----------|--------------|---------|----------------|---------|-----------|-------------|--------|--------------|--------------|-------------|--------------|
| passport1.jpg | Passport | United States | 123456789 | Doe | John | 01/01/1980 | M | New York | New York | 01/01/2015 | 01/01/2025 |
| id_card.png | ID Card | Canada | AB123456 | Smith | Jane | 15/05/1992 | F | Toronto | Ontario | 10/10/2018 | 10/10/2028 |
 ```

## Error Handling

The script includes robust error handling:

- If a file cannot be processed, an error message is displayed, and the script continues with the next file.
- If the AI response cannot be parsed as JSON, the script attempts to extract JSON from the response text.
- In case of API errors or other exceptions, detailed error messages are logged.

## Optimization

The script optimizes image processing to meet API requirements:

- Images are resized to a maximum of 2000x2000 pixels.
- Images are compressed to stay under 5MB while maintaining acceptable quality.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
