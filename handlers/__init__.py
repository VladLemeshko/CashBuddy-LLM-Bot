from .transactions import router as transactions_router
from .goals import router as goals_router
from .report import router as report_router
from .agent import router as agent_router

routers = [
    transactions_router,
    goals_router,
    report_router,
    agent_router,
]
