# Wi-Fi File Sharing

A simple Flask-based web application that allows users to share files over a local network or the internet using a session-based approach.

## Features

- **File Upload**: Upload files up to 1TB in size.
- **Session Management**: Create and join sessions with a unique 6-digit code.
- **File Access Control**: Only users in the same session can access shared files.
- **File Viewing**: View files directly in the browser without downloading.
- **Session Expiry**: Files are deleted when the session ends.

## Prerequisites

- Python 3.6 or higher
- Flask
- `humanize` module
- `pyngrok` module

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   - Open your web browser and go to `http://localhost:5501` (or the port you specified).

3. **Generate a Session Code**:
   - Click on the "Generate Session Code" button to create a new session.

4. **Join a Session**:
   - Enter the session code and your name to join the session.

5. **Upload Files**:
   - Use the upload section to share files with other users in the session.

6. **View Files**:
   - Files can be viewed directly in the browser without downloading.

7. **End Session**:
   - Click on the "End Session" button to delete all files associated with the session.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
