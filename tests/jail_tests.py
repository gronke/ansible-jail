import unittest
import sys
from mock import mock_open, patch
import __builtin__

sys.path.insert(0, '../src')
import jail
# TODO: add test for when /etc/rc.conf, /etc/jail.conf don't exist


class ModuleTestTemplate(unittest.TestCase):
    class AnsibleModule(object):
        def __init__(self, name, path, ip4_addr=None, interface=None,
                     host_hostname=None, exec_start='/bin/sh /etc/rc',
                     exec_stop='/bin/sh /etc/rc.shutdown', securelevel=3,
                     mount_devfs=True, other_config={},
                     conf_file='/etc/jail.conf', rc_file='/etc/rc.conf',
                     enabled=True, state='present'):
            if host_hostname is None:
                host_hostname = name
            self.params = {
                'name': name,
                'path': path,
                'ip4_addr': ip4_addr,
                'interface':  interface,
                'host_hostname': host_hostname,
                'exec_start': exec_start,
                'exec_stop': exec_stop,
                'securelevel': securelevel,
                'mount_devfs': mount_devfs,
                'other_config': other_config,
                'conf_file': conf_file,
                'rc_file': rc_file,
                'enabled': enabled,
                'state': state
            }


class TestGenerateJailConfig(ModuleTestTemplate):
    def test_minimal_config(self):
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "mount.devfs" = "True";\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "securelevel" = "3";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        generated_config = jail.generate_jail_conf(module)
        self.assertEqual(desired_config, generated_config)

    def test_optional_param(self):
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1',
                                    securelevel=2, host_hostname='testing')
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "host.hostname" = "testing";\n',
            '    "mount.devfs" = "True";\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "securelevel" = "2";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        generated_config = jail.generate_jail_conf(module)
        self.assertEqual(desired_config, generated_config)

    def test_other_config(self):
        module = self.AnsibleModule(name='testjail4', path='/testjail4',
                                    other_config={'children.max': 4, 'allow.raw_sockets': True})
        desired_config = [
            '#AnsibleJailBegin:testjail4\n',
            'testjail4 {\n',
            '    "allow.raw_sockets" = "True";\n',
            '    "children.max" = "4";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "host.hostname" = "testjail4";\n',
            '    "mount.devfs" = "True";\n',
            '    "path" = "/testjail4";\n',
            '    "securelevel" = "3";\n',
            '}\n',
            '#AnsibleJailEnd:testjail4\n'
        ]
        generated_config = jail.generate_jail_conf(module)
        self.assertEqual(desired_config, generated_config)


class TestGetJailConfig(ModuleTestTemplate):
    def test_minimal_config(self):
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        jail_config = '''#AnsibleJailBegin:testjail1
testjail1 {
    "path" = "/usr/local/jail/testjail1";
    "host.hostname" = "testjail1";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
}
#AnsibleJailEnd:testjail1
'''

        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)):
            loaded_config = jail.get_jail_conf(module)

        self.assertEqual(desired_config, loaded_config)

    def test_bad_config(self):
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        jail_config = '''#AnsibleJailEnd:testjail3
#AnsibleJailBegin:testjail3
#AnsibleJailBegin:testjail1
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
#AnsibleJailEnd:testjail1
#AnsibleJailEnd:testjail3
#AnsibleJailBegin:testjail3
'''

        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)):
            loaded_config = jail.get_jail_conf(module)

        self.assertEqual(desired_config, loaded_config)

    def test_more_bad_config(self):
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            '#AnsibleJailBegin:testjail3\n',
            '#AnsibleJailBegin:testjail1\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        jail_config = '''#AnsibleJailEnd:testjail3
#AnsibleJailBegin:testjail1
#AnsibleJailBegin:testjail3
#AnsibleJailBegin:testjail1
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
#AnsibleJailEnd:testjail1
#AnsibleJailEnd:testjail3
#AnsibleJailBegin:testjail3
'''

        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)):
            loaded_config = jail.get_jail_conf(module)

        self.assertEqual(desired_config, loaded_config)


class TestWriteJailConfig(ModuleTestTemplate):
    def test_update(self):
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        jail_config = '''#AnsibleJailBegin:testjail1
testjail1 {
    "path" = "/usr/local/jail/testjail1";
    "host.hostname" = "testjail1";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "2";
    "mount.devfs";
}
#AnsibleJailEnd:testjail1
'''
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "mount.devfs" = "True";\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "securelevel" = "3";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)) as m_open:
            jail.write_jail_conf(module)

        m_open().writelines.assert_called_once_with(desired_config)

    def test_adding_new(self):
        module = self.AnsibleModule(name='testjail2', path='/usr/local/jail/testjail2',
                                    ip4_addr='10.0.0.2', interface='lo1')
        jail_config = '''#AnsibleJailBegin:testjail1
testjail1 {
    "path" = "/usr/local/jail/testjail1";
    "host.hostname" = "testjail1";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
}
#AnsibleJailEnd:testjail1
'''
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n',
            '#AnsibleJailBegin:testjail2\n',
            'testjail2 {\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "host.hostname" = "testjail2";\n',
            '    "interface" = "lo1";\n',
            '    "ip4.addr" = "10.0.0.2";\n',
            '    "mount.devfs" = "True";\n',
            '    "path" = "/usr/local/jail/testjail2";\n',
            '    "securelevel" = "3";\n',
            '}\n',
            '#AnsibleJailEnd:testjail2\n'
        ]
        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)) as m_open:
            jail.write_jail_conf(module)

        m_open().writelines.assert_called_once_with(desired_config)

    def test_editing_existing(self):
        module = self.AnsibleModule(name='testjail2', path='/usr/local/jail/testjail2',
                                    ip4_addr='10.0.0.2', interface='lo1')
        jail_config = '''#AnsibleJailBegin:testjail1
testjail1 {
    "path" = "/usr/local/jail/testjail1";
    "host.hostname" = "testjail1";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
}
#AnsibleJailEnd:testjail1
#AnsibleJailBegin:testjail2
UPDATE ME!
#AnsibleJailEnd:testjail2
#AnsibleJailBegin:testjail3
testjail1 {
    "path" = "/usr/local/jail/testjail1";
    "host.hostname" = "testjail1";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
}
#AnsibleJailEnd:testjail3
'''
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n',
            '#AnsibleJailBegin:testjail2\n',
            'testjail2 {\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "host.hostname" = "testjail2";\n',
            '    "interface" = "lo1";\n',
            '    "ip4.addr" = "10.0.0.2";\n',
            '    "mount.devfs" = "True";\n',
            '    "path" = "/usr/local/jail/testjail2";\n',
            '    "securelevel" = "3";\n',
            '}\n',
            '#AnsibleJailEnd:testjail2\n',
            '#AnsibleJailBegin:testjail3\n',
            'testjail1 {\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '}\n',
            '#AnsibleJailEnd:testjail3\n'
        ]
        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)) as m_open:
            jail.write_jail_conf(module)

        m_open().writelines.assert_called_once_with(desired_config)

class TestChangeRCConfig(ModuleTestTemplate):
    def test_write_rc_nofile(self):
        start_rcconf = '''hostname="test"
'''
        end_rcconf = [
            'hostname="test"\n',
            'jail_list="testjail1"\n'
        ]
        module = self.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        with patch.object(__builtin__, 'open', mock_open(read_data=start_rcconf)) as m_open:
            jail.write_rc_jail_list(module, ['testjail1'])
        m_open().writelines.assert_called_once_with(end_rcconf)







