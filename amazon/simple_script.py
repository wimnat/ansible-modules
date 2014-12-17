import boto.ec2
import base64
from M2Crypto import RSA

instance_id = "i-18375012"

ec2 = boto.ec2.connect_to_region('us-west-2', debug=0)
#x = ec2.get_password_data("i-18375012", False)
#f = open('ec2-admin-password','w')
#f.write(base64.decodestring(x))

private_key = RSA.load_key("/root/.ssh/id_rsa_kp-wimnat-1")
print private_key.private_decrypt(base64.decodestring(ec2.get_password_data(instance_id, False)), RSA.pkcs1_padding) 

#print "X = " % x
