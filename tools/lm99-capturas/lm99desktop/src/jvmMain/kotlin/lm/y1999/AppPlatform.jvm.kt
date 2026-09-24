package lm.y1999

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

actual fun formatDate(epochMs: Long): String = SimpleDateFormat("dd/MM/yyyy", Locale.US).format(Date(epochMs))
