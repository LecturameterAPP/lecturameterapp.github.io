package shot

import androidx.compose.ui.ImageComposeScene
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.PointerEventType
import androidx.compose.ui.unit.Density
import androidx.compose.ui.use
import kotlinx.coroutines.Dispatchers
import lm.y1999.App
import lm.y1999.core.LmStore
import lm.y1999.core.PlatformFiles
import java.io.File

/**
 * Uso: main <dataDir> <density> <w> <h> action...
 * actions: tap:x,y (dp) | press:x,y | release:x,y | drag:x1,y1,x2,y2 | wait:ms | shot:path.png | long:x,y
 */
fun main(args: Array<String>) {
    System.setProperty("java.awt.headless", "true")
    val dataDir = File(args[0])
    val density = args[1].toFloat()
    val w = args[2].toInt()
    val h = args[3].toInt()
    val actions = args.drop(4)
    val store = LmStore(PlatformFiles(dataDir))
    val t0 = System.nanoTime()
    ImageComposeScene(width = w, height = h, density = Density(density), coroutineContext = Dispatchers.Unconfined) {
        App(store)
    }.use { scene ->
        fun frame() { scene.render(System.nanoTime() - t0) }
        fun pump(ms: Long) {
            val end = System.currentTimeMillis() + ms
            while (System.currentTimeMillis() < end) { frame(); Thread.sleep(16) }
            frame()
        }
        fun px(v: String) = v.toFloat() * density
        pump(600)
        for (a in actions) {
            val (kind, arg) = a.split(":", limit = 2).let { it[0] to it.getOrElse(1) { "" } }
            when (kind) {
                "wait" -> pump(arg.toLong())
                "shot" -> {
                    frame()
                    val img = scene.render(System.nanoTime() - t0)
                    File(arg).writeBytes(img.encodeToData(org.jetbrains.skia.EncodedImageFormat.PNG)!!.bytes)
                    println("shot $arg")
                }
                "tap", "press", "release", "long" -> {
                    val (x, y) = arg.split(",").map { px(it) }
                    val p = Offset(x, y)
                    when (kind) {
                        "tap" -> {
                            scene.sendPointerEvent(PointerEventType.Move, p); frame()
                            scene.sendPointerEvent(PointerEventType.Press, p); pump(60)
                            scene.sendPointerEvent(PointerEventType.Release, p); pump(450)
                        }
                        "long" -> {
                            scene.sendPointerEvent(PointerEventType.Move, p); frame()
                            scene.sendPointerEvent(PointerEventType.Press, p); pump(900)
                            scene.sendPointerEvent(PointerEventType.Release, p); pump(300)
                        }
                        "press" -> { scene.sendPointerEvent(PointerEventType.Press, p); pump(60) }
                        "release" -> { scene.sendPointerEvent(PointerEventType.Release, p); pump(300) }
                    }
                }
                "drag" -> {
                    val v = arg.split(",").map { px(it) }
                    val from = Offset(v[0], v[1]); val to = Offset(v[2], v[3])
                    scene.sendPointerEvent(PointerEventType.Press, from); pump(80)
                    val steps = 12
                    for (i in 1..steps) {
                        val f = i / steps.toFloat()
                        scene.sendPointerEvent(PointerEventType.Move, Offset(from.x + (to.x - from.x) * f, from.y + (to.y - from.y) * f)); pump(20)
                    }
                    scene.sendPointerEvent(PointerEventType.Release, to); pump(300)
                }
                "scroll" -> {
                    val v = arg.split(",")
                    val p = Offset(px(v[0]), px(v[1]))
                    repeat(v[2].toInt()) {
                        scene.sendPointerEvent(PointerEventType.Scroll, p, scrollDelta = Offset(0f, 1f)); pump(40)
                    }
                    pump(300)
                }
                "type" -> {
                    val comp = javax.swing.JPanel()
                    val conv = Class.forName("androidx.compose.ui.input.key.KeyEvent_desktopKt").getMethod("toComposeEvent", java.awt.event.KeyEvent::class.java)
                    fun ke(e: java.awt.event.KeyEvent) = androidx.compose.ui.input.key.KeyEvent(conv.invoke(null, e)!!)
                    for (ch in arg) {
                        val t = System.currentTimeMillis()
                        val code = java.awt.event.KeyEvent.getExtendedKeyCodeForChar(ch.code)
                        scene.sendKeyEvent(ke(java.awt.event.KeyEvent(comp, java.awt.event.KeyEvent.KEY_PRESSED, t, 0, code, ch)))
                        scene.sendKeyEvent(ke(java.awt.event.KeyEvent(comp, java.awt.event.KeyEvent.KEY_TYPED, t, 0, java.awt.event.KeyEvent.VK_UNDEFINED, ch)))
                        scene.sendKeyEvent(ke(java.awt.event.KeyEvent(comp, java.awt.event.KeyEvent.KEY_RELEASED, t, 0, code, ch)))
                        pump(40)
                    }
                    pump(200)
                }
                else -> error("acción desconocida: $a")
            }
        }
    }
}
