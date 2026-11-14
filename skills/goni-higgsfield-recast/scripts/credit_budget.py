"""Offline credit budget calculator; never submits a generation or buys credits."""
import argparse
import json
from decimal import Decimal, InvalidOperation


def nonnegative(value):
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError('Enter a finite number') from exc
    if not result.is_finite() or result < 0:
        raise argparse.ArgumentTypeError('Enter a finite nonnegative number')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credits', type=nonnegative, required=True)
    parser.add_argument('--video', type=nonnegative, required=True, help='Current per-attempt quote')
    parser.add_argument('--image', type=nonnegative, default=Decimal(0), help='Total image cost per finished video')
    parser.add_argument('--attempts', type=int, default=1, help='Budgeted attempts per finished video')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--reserve', type=nonnegative, default=Decimal(0))
    args = parser.parse_args()
    if args.days < 1 or args.attempts < 1 or args.reserve > args.credits:
        parser.error('days/attempts must be positive; reserve cannot exceed credits')
    cost = args.video * args.attempts + args.image
    available = args.credits - args.reserve
    total = int(available // cost) if cost else None
    print(json.dumps({
        'credits_per_finished_video': str(cost),
        'budget_after_reserve': str(available),
        'total_videos_by_budget': total,
        'average_per_day': str(Decimal(total) / args.days) if total is not None else None,
        'same_count_every_day': total // args.days if total is not None else None,
        'days': args.days,
        'note': 'Budget estimate, not a platform daily limit. Zero-credit jobs still have queue and eligibility limits.'
    }, indent=2))


if __name__ == '__main__':
    main()
