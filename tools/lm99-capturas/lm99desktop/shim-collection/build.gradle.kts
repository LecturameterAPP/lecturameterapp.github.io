plugins { kotlin("multiplatform") }
kotlin {
    jvm()
    sourceSets {
        val commonMain by getting {
            kotlin.srcDir("ANDROIDX_SRC/collection/collection/src/commonMain/kotlin")
            dependencies { api(project(":shim-annotation")) }
        }
        val jvmMain by getting {
            kotlin.srcDir("ANDROIDX_SRC/collection/collection/src/jvmMain/kotlin")
            dependencies { api("org.jspecify:jspecify:1.0.0") }
        }
        all {
            languageSettings.optIn("kotlin.RequiresOptIn")
            languageSettings.optIn("kotlin.contracts.ExperimentalContracts")
        }
    }
    compilerOptions { freeCompilerArgs.add("-Xexpect-actual-classes") }
}
java { sourceSets.getByName("jvmMain").java.srcDir("ANDROIDX_SRC/collection/collection/src/jvmMain/java") }
