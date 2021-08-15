import urllib.parse
import os
import boto3
import openpyxl
import shutil
import zipfile
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
def lambda_handler(event, context):
    data_source_bucket = event['Records'][0]['s3']['bucket']['name']
    data_source_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    os.chdir('/tmp')
    source_bucket_obj = s3.Bucket(data_source_bucket)
    source_bucket_obj.download_file(data_source_key, '/tmp/file.zip')
    zf = zipfile.ZipFile('file.zip')
    zip_file_name = data_source_key.split('/')[1].split('.zip')[0]
    firstLoop = True
    for info in zf.infolist():
        filename = info.filename.encode('cp437').decode('cp932')
        if firstLoop:
            zipdir = filename.split('/')[0]
            firstLoop = False
        if '/' in filename:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        if not os.path.isdir(filename):
            with open(filename, 'wb') as wf:
                wf.write(zf.read(info.filename))
        wb = openpyxl.load_workbook(filename)
        wb.save(filename)
    shutil.make_archive(zip_file_name, 'zip', root_dir='/tmp', base_dir=zipdir)
    upload_file = zip_file_name + '.zip'
    object_name = 'ファイルを置きたいS3のオブジェクト/' + upload_file
    s3_client.upload_file(upload_file, data_source_bucket, object_name)
    if os.path.exists(zipdir):
        shutil.rmtree(zipdir)
    if os.path.exists(upload_file):
        os.remove(upload_file)
    return None