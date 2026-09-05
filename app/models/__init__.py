from pydantic import BaseModel, Field
class OptimizeRequest(BaseModel):
    mode: str = Field('normal', pattern='^(normal|stress|crisis)$')
    scenario: str = 'Historical'
    custom_shock: float = Field(0, ge=-.5, le=.1)
class PortfolioResponse(BaseModel):
    weights: dict[str,float]
