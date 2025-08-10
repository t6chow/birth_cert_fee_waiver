# 🤖 Dignifi Form Webhook Agent

An intelligent agent that uses OpenAI GPT-5 to collect form data and send it to your n8n workflow via webhook.

## 🎯 Features

- **AI-Powered Data Extraction**: Uses OpenAI GPT-5 to intelligently extract form data from natural language input
- **Webhook Integration**: Sends collected data to your n8n workflow at `https://dignifi.app.n8n.cloud/webhook-test/fill_forms`
- **Multiple Interfaces**: Web interface (Streamlit) and command-line interface
- **Smart Validation**: Ensures data integrity and handles conditional fields
- **Real-time Processing**: Instant feedback and webhook testing capabilities

## 📋 Required Form Fields

The agent collects the following information:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name_of_requestor` | string | ✅ | Name of the person making the request |
| `homeless` | y/n | ✅ | Whether the person is homeless |
| `request_on_behalf` | y/n | ✅ | Whether the request is being made on behalf of someone else |
| `name_of_child` | string | Conditional | Child's name (only if `request_on_behalf` is 'y') |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# N8N Webhook Configuration (optional - defaults to the provided URL)
N8N_WEBHOOK_URL=https://dignifi.app.n8n.cloud/webhook-test/fill_forms
```

### 3. Run the Application

#### Web Interface (Recommended)
```bash
streamlit run app.py
```

#### Command Line Interface
```bash
python cli.py
```

## 🖥️ Usage

### Web Interface

1. Open your browser to the Streamlit app (usually `http://localhost:8501`)
2. The sidebar shows configuration status and webhook URL
3. Use either:
   - **Free Text Input**: Describe the situation naturally
   - **Structured Form**: Fill out the form fields manually
4. Click "Process and Send Webhook" to extract data and send to n8n
5. View results and conversation history

### Command Line Interface

#### Interactive Mode
```bash
python cli.py
```

#### Process Specific Input
```bash
python cli.py --input "My name is John Smith. I am not homeless. I am making this request on behalf of my child, Sarah Smith."
```

#### Test Webhook Connection
```bash
python cli.py --test
```

#### Show Form Schema
```bash
python cli.py --schema
```

#### Verbose Output
```bash
python cli.py --input "..." --verbose
```

## 📝 Input Examples

### Natural Language Examples

```
"My name is John Smith. I am not homeless. I am making this request on behalf of my child, Sarah Smith."
```

```
"I'm Jane Doe, currently homeless, and I'm requesting this for myself."
```

```
"Name: Mike Johnson, Homeless: No, Request on behalf: Yes, Child's name: Emma Johnson"
```

### Expected Output

```json
{
  "name_of_requestor": "John Smith",
  "homeless": "n",
  "request_on_behalf": "y",
  "name_of_child": "Sarah Smith"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `N8N_WEBHOOK_URL` | n8n webhook URL | `https://dignifi.app.n8n.cloud/webhook-test/fill_forms` |

### Webhook Data Format

The agent sends JSON data to your n8n webhook in this format:

```json
{
  "name_of_requestor": "string",
  "homeless": "y|n",
  "request_on_behalf": "y|n",
  "name_of_child": "string|null"
}
```

## 🛠️ Development

### Project Structure

```
├── webhook_agent.py    # Core agent logic
├── app.py             # Streamlit web interface
├── cli.py             # Command-line interface
├── requirements.txt   # Python dependencies
├── README.md         # This file
└── env_example.txt   # Environment variables template
```

### Key Components

- **`WebhookAgent`**: Main class that handles OpenAI integration and webhook communication
- **`collect_form_data()`**: Uses GPT-5 to extract structured data from natural language
- **`send_webhook()`**: Sends validated data to n8n webhook
- **`_validate_form_data()`**: Ensures data integrity and handles conditional fields

### Error Handling

The agent includes comprehensive error handling for:
- Missing API keys
- Invalid webhook URLs
- Network connectivity issues
- Malformed input data
- OpenAI API errors

## 🧪 Testing

### Test Webhook Connection
```bash
python cli.py --test
```

### Test with Sample Data
```bash
python cli.py --input "My name is Test User. I am not homeless. I am making this request for myself."
```

## 🔒 Security Considerations

- Store your OpenAI API key securely in environment variables
- Never commit API keys to version control
- The webhook URL is configurable for different environments
- All webhook communications use HTTPS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**"OpenAI API key not found"**
- Ensure you've created a `.env` file with your API key
- Check that the key is valid and has sufficient credits

**"Webhook connection failed"**
- Verify the webhook URL is correct and accessible
- Check your n8n workflow is running and accepting webhooks
- Ensure the webhook endpoint is configured to accept JSON data

**"Failed to extract form data"**
- Try rephrasing your input to be more explicit
- Use the structured form option for more reliable results
- Check that all required fields are mentioned in your input

### Getting Help

If you encounter issues:
1. Check the error messages in the application
2. Verify your configuration
3. Test the webhook connection separately
4. Review the conversation history for clues

## 🎉 Success!

Once everything is set up, you'll have a powerful AI agent that can:
- Understand natural language input
- Extract structured form data
- Validate and clean the data
- Send it to your n8n workflow
- Provide real-time feedback

The agent handles the complexity of data extraction while ensuring your n8n workflow receives clean, validated data in the expected format.
