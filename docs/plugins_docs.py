##
# This configuration file provides the source file to parse
# to extract embedded docs.
#
# This file should be updated whenever a new Testerman plugin
# is created.
##

PLUGINS = [
# label, description, filename, classname, documentation document name (for the rst file generated in docs/plugins/autogen/),
# The description is a very short one - one line max.
("XML Codec", "Encode/decode XML payloads", "codecs/Xml.py", "XmlCodec", "CodecXml"),
("RTSP Codecs", "Encode/decode RTSP requests and responses", "codecs/Rtsp.py", "RtspRequestCodec", "CodecsRtsp"),
("TCP Probe", "Send/receive TCP payloads", "probes/TcpProbe.py", "TcpProbe", "ProbeTcp"),
("UDP Probe", "Send/receive UDP packets", "probes/UdpProbe.py", "UdpProbe", "ProbeUdp"),
("SCTP Probe", "Send/receive SCTP payloads", "probes/SctpProbe.py", "SctpProbe", "ProbeSctp"),
("Directory Watcher Probe", "Watch for new/deleted files in a directory", "probes/DirWatcherProbe.py", "DirWatcherProbe", "ProbeDirWatcher"),
("File Watcher Probe", "Watch for changes in files", "probes/FileWatcherProbe.py", "FileWatcherProbe", "ProbeFileWatcher"),
("Local Execution Probe", "Execute a command in a local shell", "probes/ExecProbe.py", "ExecProbe", "ProbeExec"),
("Local Interactive Execution Probe", "Execute a command in a local shell and interact with it", "probes/ExecInteractiveProbe.py", "InteractiveExecProbe", "ProbeExecInteractive"),
("File Manager Probe", "Create, move/delete/rename files and links", "probes/FileManagerProbe.py", "FileManagerProbe", "ProbeFileManager"),
("SSH Probe", "Execute a command via a remote SSH shell", "probes/ssh/SshProbe.py", "SshProbe", "ProbeSsh"),
("Configuration File Probe", "Get or set a key in a configuration file", "probes/configurationfile/ConfigurationFileProbe.py", "ConfigFileProbe", "ProbeConfigurationFile"),
("RTP Probe", "Send/receive RTP streams", "probes/rtp/RtpProbe.py", "RtpProbe", "ProbeRtp"),
("RTSP Probe", "Act as a RTSP client over TCP", "probes/RtspClientProbe.py", "RtspClientProbe", "ProbeRtspClient"),
("LDAP Probe", "Act as a LDAP client", "probes/LdapClientProbe.py", "LdapClientProbe", "ProbeLdapClient"),
("Oracle Probe", "Oracle Database client", "probes/SqlOracleProbe.py", "OracleProbe", "ProbeSqlOracle"),
("MySQL Probe", "MySQL Database client", "probes/SqlMysqlProbe.py", "MySqlProbe", "ProbeSqlMysql"),
("HTTP Probe", "A simple HTTP client", "probes/HttpClientProbe.py", "HttpClientProbe", "ProbeHttpClient"),
("Selenium Probe", "A Web driver using Selenium RC", "probes/selenium/SeleniumProbe.py", "SeleniumProbe", "ProbeSelenium"),
]


