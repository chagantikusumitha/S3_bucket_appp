from flask import Flask, render_template, request, redirect, url_for
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)

# AWS credentials and S3 bucket information
AWS_ACCESS_KEY = 'AKIAZQ3DTJ3H6EENAPBQ'
AWS_SECRET_KEY = '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'
S3_BUCKET_NAME = 'hyderabad01'

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

def list_s3_contents(prefix=''):
    try:
        response = s3.list_objects(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        contents = response.get('Contents', [])
        return [obj['Key'] for obj in contents]
    except NoCredentialsError:
        print('AWS credentials not available or incorrect.')
    except Exception as e:
        print(f'Error listing S3 contents: {e}')
        print(f'Error response: {e.response}')
    return None

def create_folder(folder_name):
    try:
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/')
        return True
    except NoCredentialsError:
        return False

def delete_folder(folder_name):
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/')
        return True
    except NoCredentialsError:
        return False

def upload_file(file, key):
    try:
        s3.upload_fileobj(file, S3_BUCKET_NAME, key)
        return True
    except NoCredentialsError:
        return False

def delete_file(key):
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
        return True
    except NoCredentialsError:
        return False

def copy_file(source_key, destination_key):
    try:
        s3.copy_object(Bucket=S3_BUCKET_NAME, CopySource={'Bucket': S3_BUCKET_NAME, 'Key': source_key}, Key=destination_key)
        return True
    except NoCredentialsError:
        return False

def move_file(source_key, destination_key):
    if copy_file(source_key, destination_key):
        delete_file(source_key)
        return True
    return False

@app.route('/')
def index():
    contents = list_s3_contents()
    return render_template('index.html', contents=contents)

@app.route('/create_folder', methods=['POST'])
def create_folder_route():
    folder_name = request.form['folder_name']
    create_folder(folder_name)
    return redirect(url_for('index'))

@app.route('/delete_folder', methods=['POST'])
def delete_folder_route():
    folder_name = request.form['folder_name']
    delete_folder(folder_name)
    return redirect(url_for('index'))

@app.route('/upload_file', methods=['POST'])
def upload_file_route():
    file = request.files['file']
    key = request.form['key']
    upload_file(file, key)
    return redirect(url_for('index'))

@app.route('/delete_file', methods=['POST'])
def delete_file_route():
    key = request.form['key']
    delete_file(key)
    return redirect(url_for('index'))

@app.route('/copy_file', methods=['POST'])
def copy_file_route():
    source_key = request.form['source_key']
    destination_key = request.form['destination_key']
    copy_file(source_key, destination_key)
    return redirect(url_for('index'))

@app.route('/move_file', methods=['POST'])
def move_file_route():
    source_key = request.form['source_key']
    destination_key = request.form['destination_key']
    move_file(source_key, destination_key)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
