from pathlib import Path
import subprocess,json,zipfile,hashlib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');a=p/'artifacts/mindthegapps-arm13';e=p/'evidence/offline-v41'
archive=a/'MindTheGapps-13.0.0-arm-20231025_200806.zip'
jarsigner=Path('/root/t110-build/lineage20/prebuilts/jdk/jdk11/linux-x86/bin/jarsigner')
assert jarsigner.is_file()
r=subprocess.run([str(jarsigner),'-verify','-certs',str(archive)],capture_output=True,text=True)
output=r.stdout+r.stderr;(e/'mindthegapps-signature.txt').write_text(output)
assert r.returncode==0 and 'jar verified.' in output,output
with zipfile.ZipFile(archive) as z:
    (e/'mtg-CERT.RSA').write_bytes(z.read('META-INF/CERT.RSA'))
    (e/'mtg-otacert.pem').write_bytes(z.read('META-INF/com/android/otacert'))
certs=subprocess.check_output(['openssl','pkcs7','-inform','DER','-in',str(e/'mtg-CERT.RSA'),'-print_certs'])
certificate=certs[certs.index(b'-----BEGIN CERTIFICATE-----'):certs.index(b'-----END CERTIFICATE-----')+len(b'-----END CERTIFICATE-----')]
der=lambda data:subprocess.check_output(['openssl','x509','-outform','DER'],input=data)
signed=der(certificate);publisher=der((a/'release.x509.pem').read_bytes());ota=der((e/'mtg-otacert.pem').read_bytes())
assert signed==publisher==ota
record={'status':'PASS','jar_signature_valid':True,'signer_matches_publisher_release_certificate':True,'embedded_ota_certificate_matches':True,'certificate_sha256':hashlib.sha256(signed).hexdigest(),'self_signed_release_certificate':True}
(e/'mindthegapps-signature.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
