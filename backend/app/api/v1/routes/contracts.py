from fastapi import APIRouter

from app.core.schemas import ContractMetadata

router = APIRouter(prefix="/contracts")


@router.get("/metadata", response_model=ContractMetadata)
async def contract_metadata() -> ContractMetadata:
    return ContractMetadata()
