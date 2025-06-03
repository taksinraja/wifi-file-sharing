from flask import Flask, request, send_from_directory, jsonify, render_template, session
import os
from datetime import datetime
import humanize
import json
import secrets
from pyngrok import ngrok
import socket
import random

app = Flask(__name__)

# Set up ngrok authentication
ngrok.set_auth_token("2tRfM4eMBpYRP0EccDKV1x2l4tA_2JZQt8V6QEGPgEb81Rsde")

# Upload folder
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Increase upload folder path buffer size
app.config['MAX_CONTENT_PATH'] = 20 * 1024 * 1024 * 1024  # 20GB

# Increase max content length to 20GB
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 * 1024  # 20GB

# Optimize chunk size for large files (10MB chunks)
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks

# Add this after app initialization
app.secret_key = secrets.token_hex(16)

# Store active sessions with users and files
active_sessions = {}

# Add this to track uploads
def save_upload_info(filename):
    """Save upload information"""
    upload_info = {
        'filename': filename,
        'user': session.get('user_id', 'Anonymous'),
        'timestamp': datetime.now().timestamp(),
        'device': request.headers.get('User-Agent', 'Unknown Device')
    }
    
    info_file = os.path.join(UPLOAD_FOLDER, '.file_info.json')
    try:
        with open(info_file, 'r') as f:
            file_info = json.load(f)
    except:
        file_info = {}
    
    file_info[filename] = upload_info
    
    with open(info_file, 'w') as f:
        json.dump(file_info, f)

def get_file_info(filename):
    """Get upload information for a file"""
    info_file = os.path.join(UPLOAD_FOLDER, '.file_info.json')
    try:
        with open(info_file, 'r') as f:
            file_info = json.load(f)
            return file_info.get(filename, {})
    except:
        return {}

def get_file_icon(filename):
    """Return Font Awesome icon class based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        '.pdf': 'fa-file-pdf',
        '.doc': 'fa-file-word',
        '.docx': 'fa-file-word',
        '.xls': 'fa-file-excel',
        '.xlsx': 'fa-file-excel',
        '.png': 'fa-file-image',
        '.jpg': 'fa-file-image',
        '.jpeg': 'fa-file-image',
        '.gif': 'fa-file-image',
        '.zip': 'fa-file-archive',
        '.rar': 'fa-file-archive',
        '.txt': 'fa-file-alt',
    }
    return icons.get(ext, 'fa-file')

def get_file_size(filename):
    """Return human readable file size"""
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    size = os.path.getsize(path)
    return humanize.naturalsize(size)

def get_file_date(filename):
    """Return human readable file modification date"""
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    timestamp = os.path.getmtime(path)
    return humanize.naturaltime(datetime.fromtimestamp(timestamp))

def get_file_date_timestamp(filename):
    """Return file modification timestamp for sorting"""
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return str(os.path.getmtime(path))

def get_access_urls():
    """Get both local and public URLs"""
    urls = []
    
    # Get local IPs
    ip_addresses = get_ip_addresses()
    for ip in ip_addresses:
        urls.append({
            'url': f"http://{ip}:5500",
            'type': 'Local Network'
        })
    
    # Get public URL using ngrok
    try:
        # Create new tunnel
        tunnel = ngrok.connect(5500, "http")
        tunnel_url = tunnel.public_url
        
        # Add the public URL
        urls.append({
            'url': tunnel_url,
            'type': 'Public Access'
        })
        print(f"Ngrok URL: {tunnel_url}")  # Debug print
        
    except Exception as e:
        print(f"Ngrok error: {e}")
    
    return urls

def get_ip_addresses():
    """Get all local IP addresses"""
    ip_list = []
    try:
        # Get hostname first
        hostname = socket.gethostname()
        # Get IP by hostname
        ip_list.append(socket.gethostbyname(hostname))
        
        # Get all network interfaces
        interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
        for interface in interfaces:
            ip = interface[4][0]
            if not ip.startswith('127.'):  # Skip localhost
                ip_list.append(ip)
    except Exception as e:
        print(f"Error getting IPs: {e}")
    
    return list(set(ip_list))  # Remove duplicates

@app.route('/')
def home():
    # Get all access URLs
    access_urls = get_access_urls()
    
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files = [f for f in files if not f.startswith('.')]
    
    files_info = {}
    for file in files:
        info = get_file_info(file)
        files_info[file] = {
            'uploader': info.get('user', 'Anonymous'),
            'device': info.get('device', 'Unknown Device'),
            'timestamp': info.get('timestamp', 0)
        }
    
    return render_template('index.html', 
                         files=files,
                         files_info=files_info,
                         get_file_icon=get_file_icon,
                         get_file_size=get_file_size,
                         get_file_date=get_file_date,
                         get_file_date_timestamp=get_file_date_timestamp,
                         access_urls=access_urls)

@app.route('/generate_code', methods=['POST'])
def generate_code():
    """Generate a random 6-digit code for session"""
    code = str(random.randint(100000, 999999))
    active_sessions[code] = {'users': [], 'files': []}  # Initialize with empty users and files
    session['share_code'] = code
    return jsonify({"code": code}), 200

@app.route('/join_session', methods=['POST'])
def join_session():
    """Join a session using the provided code"""
    code = request.json.get('code')
    user_name = request.json.get('user_name', 'Anonymous')  # Get user name
    if code in active_sessions:
        active_sessions[code]['users'].append(user_name)  # Add user name to the session
        session['is_in_session'] = code  # Store the session code in the session
        return jsonify({"message": "Session joined successfully!", "users": active_sessions[code]['users']}), 200
    return jsonify({"message": "Invalid code!"}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part in the request.", 400

    if 'is_in_session' not in session:
        return "You must join a session to upload files.", 403

    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    # Save the file
    file.save(file_path)
    
    # Track the uploaded file in the session
    session_code = session['is_in_session']
    active_sessions[session_code]['files'].append(file.filename)

    return f"File uploaded successfully!", 200

@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    try:
        chunk = request.files['chunk']
        filename = request.form['filename']
        chunk_index = int(request.form['chunkIndex'])
        total_chunks = int(request.form['totalChunks'])

        temp_file_path = os.path.join(UPLOAD_FOLDER, f"{filename}.part")
        
        # Use buffered writing for better performance
        with open(temp_file_path, 'ab', buffering=CHUNK_SIZE) as f:
            chunk_data = chunk.read()
            f.write(chunk_data)
            f.flush()  # Ensure data is written to disk

        # If last chunk, rename the file and save upload info
        if chunk_index == total_chunks - 1:
            final_path = os.path.join(UPLOAD_FOLDER, filename)
            os.rename(temp_file_path, final_path)
            save_upload_info(filename)

        return jsonify({
            "success": True,
            "message": "Chunk uploaded successfully",
            "chunk": chunk_index,
            "total": total_chunks
        }), 200

    except Exception as e:
        # If error occurs, cleanup partial file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({
            "success": False,
            "message": f"Upload failed: {str(e)}"
        }), 500

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    if not files:
        return "<h2>No files available for download.</h2><a href='/'>Back</a>"
    file_links = "<br>".join([f"<a href='/view/{file}'>{file}</a>" for file in files])
    return f"<h2>Available Files:</h2>{file_links}<br><br><a href='/'>Back</a>"

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(file_path)
        return "File deleted successfully", 200
    except Exception as e:
        return str(e), 400

@app.route('/end_session', methods=['POST'])
def end_session():
    """End the session and delete files"""
    code = session.pop('is_in_session', None)
    if code and code in active_sessions:
        # Delete all files associated with the session
        for filename in active_sessions[code]['files']:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)  # Delete the file
        del active_sessions[code]  # Remove the session
    return jsonify({"message": "Session ended and files deleted."}), 200

@app.route('/view/<filename>', methods=['GET'])
def view_file(filename):
    """View a file without downloading"""
    session_code = session.get('is_in_session')
    if not session_code or filename not in active_sessions[session_code]['files']:
        return "You do not have permission to view this file.", 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    try:
        print("\nStarting server...")
        print("Setting up public access (this may take a few seconds)...")
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5501, debug=True)
        
    except Exception as e:
        print(f"Error: {e}")
        app.run(host='0.0.0.0', port=5501, debug=True)