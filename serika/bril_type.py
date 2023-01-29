from typing import Dict, List, Tuple, Optional, Union

JsonType = Union[Dict[str, 'JsonType'], List['JsonType'], str, int, float, bool,
                 None]
BrilType = JsonType
