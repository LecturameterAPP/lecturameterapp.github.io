pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}
dependencyResolutionManagement {
    repositories {
        mavenCentral()
    }
}
rootProject.name = "lm99desktop"
include(":shim-annotation", ":shim-collection", ":shim-arch-core", ":shim-lifecycle-common", ":shim-lifecycle-runtime", ":shim-lifecycle-viewmodel")
