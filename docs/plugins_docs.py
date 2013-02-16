##
# This configuration file provides the source file to parse
# to extract embedded docs.
#
# This file should be updated whenever a new Testerman plugin
# is created.
##

PLUGINS = [
# label, filename, classname, documentation document name (for the rst file generated in docs/plugins/autogen/),
("XML Codec", "codecs/Xml.py", "XmlCodec", "CodecXml"),
("RTSP Codecs", "codecs/Rtsp.py", "RtspRequestCodec", "CodecsRtsp"),
("TCP Probe", "probes/TcpProbe.py", "TcpProbe", "ProbeTcp"),
("UDP Probe", "probes/UdpProbe.py", "UdpProbe", "ProbeUdp"),
("SCTP Probe", "probes/SctpProbe.py", "SctpProbe", "ProbeSctp"),
]


