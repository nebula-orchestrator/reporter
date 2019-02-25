from functions.reporting.kafka import *
from functions.db.mongo import *
import datetime


# get setting from envvar with failover from config/conf.json file if envvar not set
# using skip rather then None so passing a None type will still pass a None value rather then assuming there should be
# default value thus allowing to have No value set where needed (like in the case of registry user\pass)
def get_conf_setting(setting, settings_json, default_value="skip"):
    try:
        setting_value = os.getenv(setting.upper(), settings_json.get(setting, default_value))
    except Exception as e:
        print(e, file=sys.stderr)
        print("missing " + setting + " config setting", file=sys.stderr)
        print(("missing " + setting + " config setting"))
        os._exit(2)
    if setting_value == "skip":
        print("missing " + setting + " config setting", file=sys.stderr)
        print(("missing " + setting + " config setting"))
        os._exit(2)
    return setting_value


if __name__ == "__main__":

    try:
        # read config file/envvars at startup, order preference is envvar>config file>default value (if exists)
        if os.path.exists("config/conf.json"):
            print("reading config file")
            auth_file = json.load(open("config/conf.json"))
        else:
            print("config file not found - skipping reading it and checking if needed params are given from envvars")
            auth_file = {}

        print("reading config variables")

        # the following config variables are for configure the reporter
        kafka_bootstrap_servers = get_conf_setting("kafka_bootstrap_servers", auth_file)
        kafka_security_protocol = get_conf_setting("kafka_security_protocol", auth_file, "PLAINTEXT")
        kafka_sasl_mechanism = get_conf_setting("kafka_sasl_mechanism", auth_file, None)
        kafka_sasl_plain_username = get_conf_setting("kafka_sasl_plain_username", auth_file, None)
        kafka_sasl_plain_password = get_conf_setting("kafka_sasl_plain_password", auth_file, None)
        kafka_ssl_keyfile = get_conf_setting("kafka_ssl_keyfile", auth_file, None)
        kafka_ssl_password = get_conf_setting("kafka_ssl_password", auth_file, None)
        kafka_ssl_certfile = get_conf_setting("kafka_ssl_certfile", auth_file, None)
        kafka_ssl_cafile = get_conf_setting("kafka_ssl_cafile", auth_file, None)
        kafka_ssl_crlfile = get_conf_setting("kafka_ssl_crlfile", auth_file, None)
        kafka_sasl_kerberos_service_name = get_conf_setting("kafka_sasl_kerberos_service_name", auth_file, "kafka")
        kafka_sasl_kerberos_domain_name = get_conf_setting("kafka_sasl_kerberos_domain_name", auth_file, "kafka")
        kafka_topic = get_conf_setting("kafka_topic", auth_file, "nebula-reports")
        kafka_auto_offset_reset = get_conf_setting("kafka_auto_offset_reset", auth_file, "earliest")
        kafka_group_id = get_conf_setting("kafka_group_id", auth_file, "nebula-reporter-group")
        mongo_url = get_conf_setting("mongo_url", auth_file)
        schema_name = get_conf_setting("schema_name", auth_file, "nebula")
        mongo_max_pool_size = int(get_conf_setting("mongo_max_pool_size", auth_file, "25"))
        mongo_report_ttl = int(get_conf_setting("mongo_report_ttl", auth_file, "3600"))
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
