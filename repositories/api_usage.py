from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import ApiCallLog, User, UserSubscription, Subscription
from collections import defaultdict

def get_monthly_api_usage(db: Session):
    # Get API call counts grouped by month, user, and endpoint
    usage_rows = db.query(
        ApiCallLog.user_id,
        ApiCallLog.endpoint,
        func.date_format(ApiCallLog.request_time, '%Y-%m').label('month'),
        func.count().label('call_count')
    ).group_by(
        ApiCallLog.user_id,
        ApiCallLog.endpoint,
        'month'
    ).all()

    # Get user info in bulk
    users = db.query(User).all()
    user_map = {u.id: u for u in users}

    # Get active subscriptions (latest date_to)
    subs_map = {}
    sub_records = (
        db.query(UserSubscription)
        .join(Subscription)
        .order_by(UserSubscription.user_id, UserSubscription.date_to.desc())
        .all()
    )
    for sub in sub_records:
        if sub.user_id not in subs_map:
            subs_map[sub.user_id] = sub.subscription.name

    # Organize results
    result = defaultdict(dict)
    for row in usage_rows:
        user = user_map.get(row.user_id)
        if not user:
            continue

        month = row.month
        uid = str(row.user_id)

        if uid not in result[month]:
            result[month][uid] = {
                "user_id": row.user_id,
                "username": user.username,
                "subscription": subs_map.get(row.user_id, None),
                "call": []
            }

        result[month][uid]["call"].append({
            "endpoint": row.endpoint,
            "count": row.call_count
        })

    return result
