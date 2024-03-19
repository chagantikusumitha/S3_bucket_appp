import botocore.exceptions
from flask import Flask, render_template, request, redirect, url_for
import boto3
from botocore.exceptions import NoCredentialsError
import os
from functools import wraps
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# AWS credentials and S3 bucket information
AWS_ACCESS_KEY = os.getenv('ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('SECRET_KEY')

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

def handle_exceptions(fallback_return=None, render_template='error.html'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TypeError as e:
                error_message = f"Type error occurred: {e}"
                return render_template, {'error_message': error_message, 'fallback_return': fallback_return}
            except Exception as e:
                print(f"An exception occurred: {e}")
                error_message = str(e) if not isinstance(e, tuple) else ', '.join(map(str, e))
                return render_template, {'error_message': error_message, 'fallback_return': fallback_return}
        return wrapper
    return decorator


def list_all_s3_contents():
    try:
        # List all S3 buckets
        buckets = s3.list_buckets()['Buckets']

        # Store bucket names and their contents in a dictionary
        bucket_contents = {}

        for bucket in buckets:
            bucket_name = bucket['Name']
            contents = list_s3_contents(bucket_name)

            if contents is not None:
                bucket_contents[bucket_name] = contents

        return bucket_contents

    except NoCredentialsError:
        print('AWS credentials not available or incorrect.')
    except Exception as e:
        print(f'Error listing S3 contents: {str(e)}')

    return None

def list_s3_contents(bucket_name):
    try:
        response = s3.list_objects(Bucket=bucket_name)
        contents = response.get('Contents', [])
        return [obj['Key'] for obj in contents]
    except NoCredentialsError:
        print('AWS credentials not available or incorrect.')
    except Exception as e:
        print(f'Error listing S3 contents for bucket {bucket_name}: {str(e)}')

    return None
# ... (previous code)


@app.route('/')
def index():
    bucket_contents = list_all_s3_contents()

    if bucket_contents is not None:
        return render_template('index.html', bucket_contents=bucket_contents)
    else:
        error_message = "Error listing S3 contents. Please check your AWS credentials and try again."
        return render_template('error.html', error_message=error_message)
# ... (previous code)


@app.route('/create_folder', methods=['POST'])
@handle_exceptions(fallback_return="An error occurred. Please check your inputs and try again.")
def create_folder_route():
    bucket_name = request.form['bucket_name']
    folder_name = request.form['folder_name']
    try:
        s3.put_object(Bucket=bucket_name, Key=f'{folder_name}/')
        return redirect(url_for('index', bucket_name=bucket_name))
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error.html',error_message=error_message)



@app.route('/delete_folder', methods=['POST'])
@handle_exceptions(fallback_return="An error occurred. Please check your inputs and try again.")
def delete_folder_route():
    bucket_name = request.form['bucket_name']
    folder_name = request.form['folder_name']
    try:
        s3.delete_object(Bucket=bucket_name, Key=f'{folder_name}/')
        return redirect(url_for('index', bucket_name=bucket_name))
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error.html', error_message=error_message)


@app.route('/upload_file', methods=['POST'])
def upload_file_route():
    try:
       bucket_name = request.form['bucket_name']
       folder_name = request.form.get('folder_name', '')
       file = request.files['file']
       key = file.filename

       if folder_name:
          key = f"{folder_name}/{key}"
       if file:
           # Upload the file to the specified bucket and key
           s3.upload_fileobj(file, bucket_name, key)
           return redirect(url_for('index', bucket_name=bucket_name))

        # Upload the file to the specified bucket and key
    except KeyError as e:
        error_message = f"Missing form field: {e}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error.html', error_message=error_message)


@app.route('/delete_file', methods=['POST'])
def delete_file_route():
    try:
       bucket_name = request.form['bucket_name']
       folder_name = request.form.get('folder_name', '')
       key = request.form['key']

       full_key = f"{folder_name}/{key}" if folder_name else key

    # Delete the file
       s3.delete_object(Bucket=bucket_name, Key=full_key)
       return redirect(url_for('index', bucket_name=bucket_name))
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error.html', error_message=error_message)

@app.route('/copy_file', methods=['POST'])
def copy_file_route():
    try:
        source_bucket = request.form['source_bucket']
        source_key = request.form['source_key']
        destination_bucket = request.form['destination_bucket']

        # Copy the file from the source bucket to the destination bucket
        s3.copy_object(
            Bucket=destination_bucket,
            Key=source_key,
            CopySource={'Bucket': source_bucket, 'Key': source_key}
        )

        return redirect(url_for('index', bucket_name=destination_bucket))

    except KeyError as e:
        error_message = f"Missing form field: {e}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"

    return render_template('error.html', error_message=error_message)


@app.route('/move_file', methods=['POST'])
def move_file_route():
    try:
        source_bucket = request.form['source_bucket']
        source_key = request.form['source_key']
        destination_bucket = request.form['destination_bucket']

        # Move the file from the source bucket to the destination bucket
        s3.copy_object(
            Bucket=destination_bucket,
            Key=source_key,
            CopySource={'Bucket': source_bucket, 'Key': source_key}
        )

        s3.delete_object(
            Bucket=source_bucket,
            Key=source_key
        )

        return redirect(url_for('index', bucket_name=destination_bucket))

    except KeyError as e:
        error_message = f"Missing form field: {e}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
    return render_template('error.html', error_message=error_message)

# ... (similar changes for other routes)

@app.route('/create_bucket', methods=['POST'])
@handle_exceptions(fallback_return="An error occurred. Please check your inputs and try again.")
def create_bucket_route():
    bucket_name = request.form['bucket_name']
    try:
        s3.create_bucket(Bucket=bucket_name)
        return redirect(url_for('index', bucket_name=bucket_name))
    except Exception as e:
        # Handle other general exceptions
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error.html', error_message=error_message)



@app.route('/delete_bucket', methods=['POST'])
@handle_exceptions(fallback_return="An error occurred. Please check your inputs and try again.")
def delete_bucket_route():
    bucket_name = request.form['bucket_name']
    try:
        s3.delete_bucket(Bucket=bucket_name)
        return redirect(url_for('index', bucket_name=bucket_name))
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error.html', error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)