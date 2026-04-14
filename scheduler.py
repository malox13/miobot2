import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from database import get_all_user_ids, get_activities, get_period_key, save_snapshot

logger = logging.getLogger(__name__)
ITALIAN_TZ = pytz.timezone("Europe/Rome")


def setup_scheduler(application):
    scheduler = AsyncIOScheduler(timezone=ITALIAN_TZ)

    # Save daily snapshots at 23:55 Italian time (before midnight reset)
    scheduler.add_job(
        save_all_snapshots,
        CronTrigger(hour=23, minute=55, timezone=ITALIAN_TZ),
        id="save_daily_snapshots",
        replace_existing=True,
    )

    # Save weekly snapshots Sunday 23:55
    scheduler.add_job(
        save_all_snapshots,
        CronTrigger(day_of_week="sun", hour=23, minute=55, timezone=ITALIAN_TZ),
        id="save_weekly_snapshots",
        replace_existing=True,
    )

    # Save monthly snapshots last day of month 23:55
    scheduler.add_job(
        save_all_snapshots,
        CronTrigger(day="last", hour=23, minute=55, timezone=ITALIAN_TZ),
        id="save_monthly_snapshots",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler avviato (fuso orario: Europe/Rome)")


async def save_all_snapshots():
    """Saves a snapshot for all users and activities before reset."""
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        activities = get_activities(user_id)
        for act in activities:
            period_key = get_period_key(act["timeframe"])
            try:
                save_snapshot(user_id, act["id"], period_key)
            except Exception as e:
                logger.error(f"Errore snapshot user={user_id} act={act['id']}: {e}")
    logger.info(f"Snapshot salvati per {len(user_ids)} utenti")
