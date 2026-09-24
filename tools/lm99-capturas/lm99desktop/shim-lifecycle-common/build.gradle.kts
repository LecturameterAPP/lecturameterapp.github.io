plugins { kotlin("multiplatform") }
kotlin {
    jvm()
    sourceSets {
        val commonMain by getting {
            kotlin.srcDir("ANDROIDX_SRC/lifecycle/lifecycle-common/src/commonMain/kotlin")
            dependencies { api(project(":shim-annotation")); api("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.1"); implementation("org.jetbrains.kotlinx:atomicfu:0.23.2") }
        }
        val jvmMain by getting {
            kotlin.srcDir("ANDROIDX_SRC/lifecycle/lifecycle-common/src/jvmMain/kotlin")
            dependencies { api("org.jspecify:jspecify:1.0.0") }
        }
        all { languageSettings.optIn("kotlin.RequiresOptIn"); languageSettings.optIn("kotlin.contracts.ExperimentalContracts") }
    }
    compilerOptions { freeCompilerArgs.add("-Xexpect-actual-classes") }
}
java { sourceSets.getByName("jvmMain").java.srcDir("ANDROIDX_SRC/lifecycle/lifecycle-common/src/jvmMain/java") }
