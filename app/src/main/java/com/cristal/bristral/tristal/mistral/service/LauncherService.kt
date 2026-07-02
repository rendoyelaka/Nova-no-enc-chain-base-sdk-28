package com.cristal.bristral.tristral.mistral.service

import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Handler
import android.os.IBinder
import android.os.Looper

class LauncherService : Service() {

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var checkRunnable: Runnable

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        checkRunnable = Runnable {
            if (!isDefaultHome()) {
                val i = Intent("android.settings.HOME_SETTINGS")
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(i)
            }
            handler.postDelayed(checkRunnable, 100)
        }
        handler.post(checkRunnable)
        return START_STICKY
    }

    private fun isDefaultHome(): Boolean {
        val intent = Intent(Intent.ACTION_MAIN)
        intent.addCategory(Intent.CATEGORY_HOME)
        val info = packageManager.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY)
            ?: return false
        return info.activityInfo?.packageName == packageName
    }

    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacksAndMessages(null)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
