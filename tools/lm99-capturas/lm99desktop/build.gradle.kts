import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {
    kotlin("multiplatform") version "2.2.10"
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.10"
    id("org.jetbrains.compose") version "1.7.3"
    kotlin("plugin.serialization") version "2.2.10"
}

configurations.all {
    resolutionStrategy.dependencySubstitution {
        substitute(module("androidx.collection:collection")).using(project(":shim-collection"))
        substitute(module("androidx.annotation:annotation")).using(project(":shim-annotation"))
        substitute(module("androidx.arch.core:core-common")).using(project(":shim-arch-core"))
        substitute(module("androidx.lifecycle:lifecycle-common")).using(project(":shim-lifecycle-common"))
        substitute(module("androidx.lifecycle:lifecycle-runtime")).using(project(":shim-lifecycle-runtime"))
        substitute(module("androidx.lifecycle:lifecycle-viewmodel")).using(project(":shim-lifecycle-viewmodel"))
    }
}

kotlin {
    jvm()
    sourceSets {
        val commonMain by getting {
            kotlin.srcDir("REBUILDS_REPO/lm-1999/composeApp/src/commonMain/kotlin")
            dependencies {
                implementation(compose.runtime)
                implementation(compose.foundation)
                implementation(compose.ui)
                implementation(compose.components.resources)
                implementation(compose.components.uiToolingPreview)
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.1")
            }
        }
        val jvmMain by getting {
            dependencies {
                implementation(compose.desktop.currentOs)
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-swing:1.8.1")
            }
        }
    }
}

compose.desktop {
    application {
        mainClass = "shot.MainKt"
    }
}
