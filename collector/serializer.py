from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MetaInfo(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    library: Dict[str, str]
    host: Dict[str, str]
    notes: Optional[str] = None

class RequestConfig(BaseModel):
    max_output_tokens: int
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    seed: Optional[int] = None
    store: bool = False

class NormalizationConfig(BaseModel):
    enabled: bool = False
    rules: Dict[str, bool] = Field(default_factory=dict)

class ConfigInfo(BaseModel):
    model: str
    prompt: str
    n: int
    concurrency: int
    request: RequestConfig
    normalization: NormalizationConfig

class ErrorInfo(BaseModel):
    type: str
    message: str
    http_status: Optional[int] = None

class DeviationInfo(BaseModel):
    enabled: bool = False
    is_deviation: Optional[bool] = None
    matched_expected: Optional[str] = None

class LogprobDetail(BaseModel):
    token: str
    logprob: float
    bytes: Optional[List[int]] = None

class LogprobContent(BaseModel):
    token: str
    logprob: float
    bytes: Optional[List[int]] = None
    top_logprobs: Optional[List[LogprobDetail]] = Field(default_factory=list)

class RunResult(BaseModel):
    id: int
    text: str
    raw_text: Optional[str] = None
    status: str = "ok"
    error: Optional[ErrorInfo] = None
    usage: Optional[Dict[str, Optional[int]]] = None
    deviation: Optional[DeviationInfo] = None
    logprobs: Optional[List[LogprobContent]] = None

class Node(BaseModel):
    id: int
    depth: int

class Edge(BaseModel):
    from_node: int = Field(..., alias="from")
    to_node: int = Field(..., alias="to")
    ch: str
    count: int
    p: Optional[float] = None

    class Config:
        populate_by_name = True

class GraphInfo(BaseModel):
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)

class DepthStat(BaseModel):
    depth: int
    total_transitions: int
    unique_chars: int
    top_chars: List[Dict[str, Any]] = Field(default_factory=list)
    entropy_bits: float

class StatsInfo(BaseModel):
    totals: Dict[str, int]
    depth_stats: List[DepthStat] = Field(default_factory=list)
    deviations: Optional[Dict[str, Any]] = None

class CollectorOutput(BaseModel):
    meta: MetaInfo
    config: ConfigInfo
    runs: List[RunResult] = Field(default_factory=list)
    graph: GraphInfo
    stats: StatsInfo
