from functions.reporting.kafka import *
from functions.db.mongo import *
import datetime
from parse_it import ParseIt

if __name__ == "__main__":

    try:
        print("reading config variables")
        parser = ParseIt(config_folder_location="config", recurse=True)

        # the following config variables are for configure the reporter
        kafka_bootstrap_servers = parser.read_configuration_variable("kafka_bootstrap_servers", required=True)
        kafka_security_protocol = parser.read_configuration_variable("kafka_security_protocol",
                                                                     default_value="PLAINTEXT")
        kafka_sasl_mechanism = parser.read_configuration_variable("kafka_sasl_mechanism",  default_value=None)
        kafka_sasl_plain_username = parser.read_configuration_variable("kafka_sasl_plain_username",  default_value=None)
        kafka_sasl_plain_password = parser.read_configuration_variable("kafka_sasl_plain_password",  default_value=None)
        kafka_ssl_keyfile = parser.read_configuration_variable("kafka_ssl_keyfile",  default_value=None)
        kafka_ssl_password = parser.read_configuration_variable("kafka_ssl_password",  default_value=None)
        kafka_ssl_certfile = parser.read_configuration_variable("kafka_ssl_certfile",  default_value=None)
        kafka_ssl_cafile = parser.read_configuration_variable("kafka_ssl_cafile",  default_value=None)
        kafka_ssl_crlfile = parser.read_configuration_variable("kafka_ssl_crlfile",  default_value=None)
        kafka_sasl_kerberos_service_name = parser.read_configuration_variable("kafka_sasl_kerberos_service_name",
                                                                              default_value="kafka")
        kafka_sasl_kerberos_domain_name = parser.read_configuration_variable("kafka_sasl_kerberos_domain_name",
                                                                             default_value="kafka")
        kafka_topic = parser.read_configuration_variable("kafka_topic",  default_value="nebula-reports")
        kafka_auto_offset_reset = parser.read_configuration_variable("kafka_auto_offset_reset",
                                                                     default_value="earliest")
        kafka_group_id = parser.read_configuration_variable("kafka_group_id",  default_value="nebula-reporter-group")
        mongo_url = parser.read_configuration_variable("mongo_url", required=True)
        schema_name = parser.read_configuration_variable("schema_name",  default_value="nebula")
        mongo_max_pool_size = parser.read_configuration_variable("mongo_max_pool_size",  default_value=25)
        mongo_report_ttl = parser.read_configuration_variable("mongo_report_ttl",  default_value=3600)
    except Exception as e:
        print(e, file=sys.stderr)
        print("error reading config settings")
        os._exit(2)

    try:
        print("creating reporting kafka connection object")
        kafka_consumer_object = kafka_consume(kafka_bootstrap_servers,
                                              security_protocol=kafka_security_protocol,
                                              sasl_mechanism=kafka_sasl_mechanism,
                                              sasl_plain_username=kafka_sasl_plain_username,
                                              sasl_plain_password=kafka_sasl_plain_password,
                                              ssl_keyfile=kafka_ssl_keyfile,
                                              ssl_password=kafka_ssl_password,
                                              ssl_certfile=kafka_ssl_certfile,
                                              ssl_cafile=kafka_ssl_cafile,
                                              ssl_crlfile=kafka_ssl_crlfile,
                                              sasl_kerberos_service_name=kafka_sasl_kerberos_service_name,
                                              sasl_kerberos_domain_name=kafka_sasl_kerberos_domain_name,
                                              topic=kafka_topic,
                                              auto_offset_reset=kafka_auto_offset_reset,
                                              group_id=kafka_group_id)
    except Exception as e:
        print(e, file=sys.stderr)
        print("failed creating reporting kafka connection object - exiting")
        os._exit(2)

    try:
        # login to db at startup
        mongo_connection = MongoConnection(mongo_url, schema_name, max_pool_size=mongo_max_pool_size)
        print("opened MongoDB connection")
    except Exception as e:
        print(e, file=sys.stderr)
        print("failed creating backend DB connection object - exiting")
        os._exit(2)

    try:
        # ensure mongo is indexed properly
        mongo_connection.mongo_create_ttl_index("report_insert_date", mongo_report_ttl)
    except Exception as e:
        print(e, file=sys.stderr)
        print("failed creating mongo ttl index - exiting")
        os._exit(2)

    print("starting to digest messages from kafka")
    try:
        for message in kafka_consumer_object:
            message_body = message.value
            message_body["report_insert_date"] = datetime.datetime.utcnow()
            mongo_connection.mongo_add_report(message_body)
    except Exception as e:
        print(e, file=sys.stderr)
        print("failed writing report into mongo - exiting")
        os._exit(2)
