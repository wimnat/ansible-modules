To test:
python /opt/codebase/ansible-project/ansible/hacking/test-module -m /opt/codebase/wimnat/ansible-modules/elastictranscoder/elastictranscoder.py -a "state=present name=tester input_bucket=input.bucket output_bucket=output.bucket region=us-west-2 role=arn:aws:iam::0000000000:role/Elastic_Transcoder_Default_Role"

change 00000000:role to valid iam role


TO DO:
Create a pipeline object for comparison to see if an update to config is required
