from kafka import KafkaConsumer
import sys, json


class KafkaConnection:

    def __init__(self, bootstrap_servers, security_protocol="PLAINTEXT", sasl_mechanism=None, sasl_plain_username=None,
                 sasl_plain_password=None, ssl_keyfile=None, ssl_password=None, ssl_certfile=None, ssl_cafile=None,
                 ssl_crlfile=None, sasl_kerberos_service_name="kafka", sasl_kerberos_domain_name="kafka",
                 group_id="nebula-reporter-group", topic="nebula-reports", auto_offset_reset='earliest'):
        self.topic = topic
        self.group_id = group_id
        self.consumer = KafkaConsumer(self.topic, group_id=self.group_id, security_protocol=security_protocol,
                                      value_deserializer=lambda m: json.loads(m.decode('ascii')),
                                      bootstrap_servers=bootstrap_servers, ssl_cafile=ssl_cafile,
                                      sasl_mechanism=sasl_mechanism, sasl_plain_username=sasl_plain_username,
                                      sasl_plain_password=sasl_plain_password, ssl_keyfile=ssl_keyfile,
                                      ssl_password=ssl_password, ssl_certfile=ssl_certfile, ssl_crlfile=ssl_crlfile,
                                      sasl_kerberos_service_name=sasl_kerberos_service_name,
                                      sasl_kerberos_domain_name=sasl_kerberos_domain_name,
                                      auto_offset_reset=auto_offset_reset)
