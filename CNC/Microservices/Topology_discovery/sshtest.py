import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.2.64', username='sys-admin', password='sys-admin')
#ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('ip -f inet addr show eth0 | sed -En -e \'s/.*inet ([0-9.]+).*/\\1/p\'')
#data = ssh_stdout.readlines()
#print(data)
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo lldpcli show neighbors -f json',get_pty=True)
ssh_stdin.write('sys-admin\n')
ssh_stdin.flush()
data = ssh_stdout.readlines()
print("DATA----------")
print(data)