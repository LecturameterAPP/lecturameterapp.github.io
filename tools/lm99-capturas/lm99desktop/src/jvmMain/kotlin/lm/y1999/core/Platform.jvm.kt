package lm.y1999.core

import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.toComposeImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

actual fun nowMillis(): Long = System.currentTimeMillis()

actual class PlatformFiles(root: File) {
    private val rootDir: File = root.apply { mkdirs() }
    actual val dataDir: String get() = rootDir.absolutePath
    private fun resolve(path: String): File = File(rootDir, path).also { it.parentFile?.mkdirs() }
    actual fun readText(path: String): String? = resolve(path).let { if (it.exists()) it.readText() else null }
    actual fun writeText(path: String, text: String) { resolve(path).writeText(text) }
    actual fun rename(fromPath: String, toPath: String) {
        val from = resolve(fromPath); val to = resolve(toPath)
        if (!from.renameTo(to)) { to.writeBytes(from.readBytes()); from.delete() }
    }
    actual fun readBytes(path: String): ByteArray? = resolve(path).let { if (it.exists()) it.readBytes() else null }
    actual fun writeBytes(path: String, bytes: ByteArray) { resolve(path).writeBytes(bytes) }
    actual fun delete(path: String) { resolve(path).delete() }
    actual fun exists(path: String): Boolean = resolve(path).exists()
}

actual fun decodeImage(bytes: ByteArray): ImageBitmap? = try {
    org.jetbrains.skia.Image.makeFromEncoded(bytes).toComposeImageBitmap()
} catch (_: Throwable) { null }

actual suspend fun downloadBytes(url: String): ByteArray? = withContext(Dispatchers.IO) {
    try {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 15000; c.readTimeout = 15000; c.instanceFollowRedirects = true
        c.setRequestProperty("User-Agent", "Mozilla/5.0")
        c.connect()
        if (c.responseCode in 200..299) c.inputStream.use { it.readBytes() } else null
    } catch (_: Throwable) { null }
}

@Composable
actual fun rememberImagePicker(onResult: (ByteArray?) -> Unit): () -> Unit = { onResult(null) }

@Composable
actual fun rememberOpenTextFile(mimeTypes: List<String>, onResult: (text: String?, cancelled: Boolean) -> Unit): () -> Unit = { onResult(null, true) }

@Composable
actual fun rememberCreateTextFile(
    mimeType: String,
    suggestedName: String,
    textProvider: () -> String,
    onResult: (ok: Boolean, cancelled: Boolean) -> Unit,
): () -> Unit = { onResult(false, true) }
