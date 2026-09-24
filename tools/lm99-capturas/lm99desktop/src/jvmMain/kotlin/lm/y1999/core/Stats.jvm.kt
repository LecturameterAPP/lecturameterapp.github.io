package lm.y1999.core

import java.util.Calendar
import java.util.TimeZone

actual fun localDayIndex(epochMs: Long): Long {
    val cal = Calendar.getInstance(TimeZone.getDefault())
    cal.timeInMillis = epochMs
    cal.set(Calendar.HOUR_OF_DAY, 0); cal.set(Calendar.MINUTE, 0); cal.set(Calendar.SECOND, 0); cal.set(Calendar.MILLISECOND, 0)
    return (cal.timeInMillis + cal.timeZone.getOffset(cal.timeInMillis)) / 86_400_000L
}

actual fun hourOfDay(epochMs: Long): Int {
    val cal = Calendar.getInstance(TimeZone.getDefault())
    cal.timeInMillis = epochMs
    return cal.get(Calendar.HOUR_OF_DAY)
}
