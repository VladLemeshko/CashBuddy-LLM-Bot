from .transactions import router as transactions_router
from .goals import router as goals_router
from .report import router as report_router
from .agent import router as agent_router
from .profile_survey import router as profile_survey_router
from .menu import router as menu_router

routers = [
    transactions_router,
    goals_router,
    report_router,
    agent_router,
    profile_survey_router,
    menu_router,
]
