from dataclasses import dataclass

@dataclass
class StreamHandlerConfig :
    read_size: int = 4096
    delimiter: bytes = b'\xCA\xFE\xBA\xBE'
    max_payload_size: int = 10 * 1024 * 1024 # 10Mb

    trust: bool = False
    max_fail_count: int = 5

@dataclass
class MessageHandlerConfig :
    comm_count_limit: int = 300
    comm_count_limit_reset_period_seconds: float = 60
    no_comm_limit: float = 3600
    no_comm_limit_check_period_seconds: float = 1800
