package com.cristal.bristral.tristral.mistral

import android.app.Application
import android.content.Intent
import com.cristal.bristral.tristral.mistral.service.LauncherService

class LauncherApplication : Application() {

    companion object {
        lateinit var instance: LauncherApplication
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        startService(Intent(this, LauncherService::class.java))
    }
}
