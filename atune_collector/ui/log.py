import logging

logname = "/var/log/atune_collector.log"

logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

logging.info("Running atune_collector logging")

logger = logging.getLogger('atune_collector')
