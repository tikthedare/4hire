from django.db.models import Avg, Count


def refresh_listing_ratings(coach_id):
    """Store a cached public average on the coach listing. Hidden reviews are excluded."""
    from listings.models import Listing
    from reviews.models import Review

    stats = Review.objects.filter(coach_id=coach_id, hidden=False).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )
    Listing.objects.filter(coach_id=coach_id).update(
        rating_count=stats["count"] or 0,
        rating_avg=stats["avg"],
    )
