namespace ForexIntelligence.Application.Services;

public static class ForexMarketSchedule
{
    private static readonly TimeSpan WeeklyOpenUtc = TimeSpan.FromHours(22);
    private static readonly TimeSpan WeeklyCloseUtc = TimeSpan.FromHours(22);

    public static bool IsOpen(DateTimeOffset utcTime)
    {
        if (utcTime.Offset != TimeSpan.Zero)
        {
            throw new ArgumentException("Market schedule time must use UTC.", nameof(utcTime));
        }

        return utcTime.DayOfWeek switch
        {
            DayOfWeek.Saturday => false,
            DayOfWeek.Sunday => utcTime.TimeOfDay >= WeeklyOpenUtc,
            DayOfWeek.Friday => utcTime.TimeOfDay < WeeklyCloseUtc,
            _ => true
        };
    }
}
