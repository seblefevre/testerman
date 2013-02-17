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
("TCP Probe", "Send/Receive TCP payloads", "probes/TcpProbe.py", "TcpProbe", "ProbeTcp"),
("UDP Probe", "Send/Receive UDP packets", "probes/UdpProbe.py", "UdpProbe", "ProbeUdp"),
("SCTP Probe", "Send/receive SCTP payloads", "probes/SctpProbe.py", "SctpProbe", "ProbeSctp"),
("Directory Watcher Probe", "Watch for new/deleted files in a directory", "probes/DirWatcherProbe.py", "DirWatcherProbe", "ProbeDirWatcher"),
("File Watcher Probe", "Watch for changes in files", "probes/FileWatcherProbe.py", "FileWatcherProbe", "ProbeFileWatcher"),
("Local Execution Probe", "Execute a command in a local shell", "probes/ExecProbe.py", "ExecProbe", "ProbeExec"),
("Local Interactive Execution Probe", "Execute a command in a local shell and interact with it", "probes/ExecInteractiveProbe.py", "InteractiveExecProbe", "ProbeExecInteractive"),
("File Manager Probe", "Create, move/delete/rename files and links", "probes/FileManagerProbe.py", "FileManagerProbe", "ProbeFileManager"),
("SSH Probe", "Execute a command via a remote SSH shell", "probes/ssh/SshProbe.py", "SshProbe", "ProbeSsh"),
]


