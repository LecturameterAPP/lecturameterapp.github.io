plugins { kotlin("multiplatform") }
kotlin {
    jvm()
    sourceSets {
        val commonMain by getting { kotlin.srcDir("ANDROIDX_SRC/annotation/annotation/src/commonMain/kotlin") }
        val jvmMain by getting { kotlin.srcDir("ANDROIDX_SRC/annotation/annotation/src/jvmMain/kotlin") }
    }
    compilerOptions { freeCompilerArgs.add("-Xexpect-actual-classes") }
}
