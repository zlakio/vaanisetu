package com.example.vaanisetu

import android.Manifest
import android.content.pm.PackageManager
import android.media.*
import android.os.Bundle
import android.view.MotionEvent
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.asRequestBody
import org.json.JSONObject
import java.io.File
import java.io.IOException

class MainActivity : AppCompatActivity() {

    private val SERVER = "http://10.71.197.207:5000"

    private lateinit var lessonSpinner:       Spinner
    private lateinit var modeSpinner:         Spinner
    private lateinit var stepText:            TextView
    private lateinit var statusText:          TextView
    private lateinit var hindiText:           TextView
    private lateinit var santaliText:         TextView
    private lateinit var latencyText:         TextView
    private lateinit var comprehensionSignal: TextView
    private lateinit var recordButton:        Button
    private lateinit var nextStepButton:      Button
    private lateinit var studentResponseInput:EditText
    private lateinit var submitResponseButton:Button
    private lateinit var worksheetButton:     Button
    private lateinit var summaryButton:       Button
    private lateinit var summaryText:         TextView

    private var recorder:  AudioRecord? = null
    private var isRecording = false
    private val client = OkHttpClient.Builder()
        .callTimeout(180, java.util.concurrent.TimeUnit.SECONDS).build()

    private val SAMPLE_RATE = 16000
    private val CHANNEL     = AudioFormat.CHANNEL_IN_MONO
    private val ENCODING    = AudioFormat.ENCODING_PCM_16BIT

    private var currentSessionId = ""
    private var lastHindi        = ""
    private var lastSantali      = ""
    private var lessonList       = listOf<JSONObject>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        bindViews()
        requestMicPermission()
        setupModeSpinner()
        loadLessons()
        setupButtons()
    }

    private fun bindViews() {
        lessonSpinner        = findViewById(R.id.lessonSpinner)
        modeSpinner          = findViewById(R.id.modeSpinner)
        stepText             = findViewById(R.id.stepText)
        statusText           = findViewById(R.id.statusText)
        hindiText            = findViewById(R.id.hindiText)
        santaliText          = findViewById(R.id.santaliText)
        latencyText          = findViewById(R.id.latencyText)
        comprehensionSignal  = findViewById(R.id.comprehensionSignal)
        recordButton         = findViewById(R.id.recordButton)
        nextStepButton       = findViewById(R.id.nextStepButton)
        studentResponseInput = findViewById(R.id.studentResponseInput)
        submitResponseButton = findViewById(R.id.submitResponseButton)
        worksheetButton      = findViewById(R.id.worksheetButton)
        summaryButton        = findViewById(R.id.summaryButton)
        summaryText          = findViewById(R.id.summaryText)
    }

    private fun requestMicPermission() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED)
            ActivityCompat.requestPermissions(
                this, arrayOf(Manifest.permission.RECORD_AUDIO), 1)
    }

    private fun setupModeSpinner() {
        val modes = listOf("Lesson Script", "Activity Instruction", "Assessment Prompt")
        modeSpinner.adapter = ArrayAdapter(
            this, android.R.layout.simple_spinner_item, modes).also {
            it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item) }
    }

    private fun loadLessons() {
        Thread {
            try {
                val req = Request.Builder().url("$SERVER/lessons").get().build()
                client.newCall(req).execute().use { resp ->
                    if (resp.isSuccessful) {
                        val json    = JSONObject(resp.body?.string() ?: "{}")
                        val arr     = json.getJSONArray("lessons")
                        val items   = mutableListOf<String>()
                        val objects = mutableListOf<JSONObject>()
                        for (i in 0 until arr.length()) {
                            val l = arr.getJSONObject(i)
                            items.add("Grade ${l.getString("grade")}: ${l.getString("title")}")
                            objects.add(l)
                        }
                        lessonList = objects
                        runOnUiThread {
                            lessonSpinner.adapter = ArrayAdapter(
                                this, android.R.layout.simple_spinner_item, items).also {
                                it.setDropDownViewResource(
                                    android.R.layout.simple_spinner_dropdown_item)
                            }
                            statusText.text = "✅ ${items.size} lessons loaded. Select a lesson and start."
                        }
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { statusText.text = "❌ Cannot reach server — check WiFi and IP" }
            }
        }.start()
    }

    private fun setupButtons() {
        lessonSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>, v: View?, pos: Int, id: Long) {
                if (lessonList.isNotEmpty()) startLesson(lessonList[pos])
            }
            override fun onNothingSelected(p: AdapterView<*>) {}
        }

        recordButton.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> { startRecording(); true }
                MotionEvent.ACTION_UP   -> { stopAndTranslate(); true }
                else -> false
            }
        }

        nextStepButton.setOnClickListener { advanceStep() }

        submitResponseButton.setOnClickListener {
            val resp = studentResponseInput.text.toString().trim()
            if (resp.isNotEmpty() && currentSessionId.isNotEmpty())
                submitStudentResponse(resp)
            else Toast.makeText(this, "Enter a response first", Toast.LENGTH_SHORT).show()
        }

        worksheetButton.setOnClickListener {
            if (lastHindi.isNotEmpty()) generateWorksheet()
            else Toast.makeText(this, "Record a translation first", Toast.LENGTH_SHORT).show()
        }

        summaryButton.setOnClickListener {
            if (currentSessionId.isNotEmpty()) fetchSessionSummary()
            else Toast.makeText(this, "Start a lesson first", Toast.LENGTH_SHORT).show()
        }
    }

    private fun startLesson(lesson: JSONObject) {
        val grade = lesson.getString("grade")
        val topic = lesson.getString("topic")
        runOnUiThread { statusText.text = "⏳ Starting lesson..." }

        Thread {
            try {
                val body = RequestBody.create(
                    "application/json".toMediaTypeOrNull(),
                    """{"grade":"$grade","topic":"$topic"}""")
                val req = Request.Builder().url("$SERVER/session/start").post(body).build()
                client.newCall(req).execute().use { resp ->
                    if (resp.isSuccessful) {
                        val json = JSONObject(resp.body?.string() ?: "{}")
                        currentSessionId = json.getString("session_id")
                        val stepData = json.getJSONObject("step_data")
                        runOnUiThread {
                            statusText.text = "✅ Lesson started: ${json.getString("lesson_title")}"
                            stepText.text = "Step 1/${json.getInt("total_steps")}: " +
                                    "${stepData.getString("type").replace("_"," ")} — " +
                                    stepData.getString("note")
                            comprehensionSignal.visibility = View.GONE
                            summaryText.visibility = View.GONE
                        }
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { statusText.text = "❌ Error starting lesson" }
            }
        }.start()
    }

    private fun startRecording() {
        val bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, ENCODING)
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) return
        recorder = AudioRecord(MediaRecorder.AudioSource.MIC,
            SAMPLE_RATE, CHANNEL, ENCODING, bufSize)
        recorder?.startRecording()
        isRecording = true
        runOnUiThread {
            statusText.text = "🔴 Recording..."
            recordButton.text = "RELEASE TO TRANSLATE"
            recordButton.setBackgroundColor(
                resources.getColor(android.R.color.holo_orange_dark, null))
        }
    }

    private fun stopAndTranslate() {
        isRecording = false
        recorder?.stop()
        val bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, ENCODING)
        val audioData = mutableListOf<Short>()
        val buffer = ShortArray(bufSize)
        var read: Int
        do {
            read = recorder?.read(buffer, 0, bufSize) ?: 0
            if (read > 0) audioData.addAll(buffer.take(read))
        } while (read > 0)
        recorder?.release(); recorder = null

        val wavFile = File(cacheDir, "hindi_input.wav")
        writeWav(wavFile, audioData.toShortArray())

        runOnUiThread {
            statusText.text = "⏳ Translating..."
            recordButton.text = "HOLD TO SPEAK (Hindi)"
            recordButton.setBackgroundColor(
                resources.getColor(android.R.color.holo_red_dark, null))
        }

        val modeKey = when (modeSpinner.selectedItem.toString()) {
            "Activity Instruction" -> "activity_instruction"
            "Assessment Prompt"    -> "assessment_prompt"
            else                   -> "lesson_script"
        }

        Thread {
            try {
                val body = MultipartBody.Builder().setType(MultipartBody.FORM)
                    .addFormDataPart("audio", "hindi_input.wav",
                        wavFile.asRequestBody("audio/wav".toMediaTypeOrNull()))
                    .addFormDataPart("mode", modeKey)
                    .addFormDataPart("session_id", currentSessionId)
                    .build()
                val req = Request.Builder().url("$SERVER/translate/audio").post(body).build()
                val t0  = System.currentTimeMillis()
                client.newCall(req).execute().use { resp ->
                    val totalMs = System.currentTimeMillis() - t0
                    if (resp.isSuccessful) {
                        val json = JSONObject(resp.body?.string() ?: "{}")
                        lastHindi   = json.getString("hindi_text")
                        lastSantali = json.getString("santali_text")
                        val latency = json.getJSONObject("latency")
                        playAudio("$SERVER/audio/output")
                        runOnUiThread {
                            hindiText.text   = lastHindi
                            santaliText.text = lastSantali
                            latencyText.text = "⚡ NMT: ${latency.getDouble("nmt_seconds")}s | " +
                                    "TTS: ${latency.getDouble("tts_seconds")}s | " +
                                    "Total: ${String.format("%.1f", totalMs/1000.0)}s"
                            statusText.text = "✅ Playing Santali translation"
                        }
                    } else {
                        runOnUiThread { statusText.text = "❌ Server error ${resp.code}" }
                    }
                }
            } catch (e: IOException) {
                runOnUiThread { statusText.text = "❌ Connection error — check server IP" }
            }
        }.start()
    }

    private fun advanceStep() {
        if (currentSessionId.isEmpty()) return
        Thread {
            try {
                val body = RequestBody.create(
                    "application/json".toMediaTypeOrNull(),
                    """{"session_id":"$currentSessionId"}""")
                val req = Request.Builder().url("$SERVER/session/next").post(body).build()
                client.newCall(req).execute().use { resp ->
                    val json = JSONObject(resp.body?.string() ?: "{}")
                    runOnUiThread {
                        if (json.optBoolean("completed", false)) {
                            stepText.text = "Lesson complete! Tap SESSION SUMMARY."
                            statusText.text = "✅ All steps completed"
                        } else {
                            val s = json.getJSONObject("step_data")
                            stepText.text = "Step ${json.getInt("current_step")+1}/" +
                                    "${json.getInt("total_steps")}: " +
                                    "${s.getString("type").replace("_"," ")} — " +
                                    s.getString("note")
                        }
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { statusText.text = "❌ Error advancing step" }
            }
        }.start()
    }

    private fun submitStudentResponse(response: String) {
        Thread {
            try {
                val body = RequestBody.create(
                    "application/json".toMediaTypeOrNull(),
                    """{"session_id":"$currentSessionId","response":"$response"}""")
                val req = Request.Builder()
                    .url("$SERVER/session/response").post(body).build()
                client.newCall(req).execute().use { resp ->
                    val json   = JSONObject(resp.body?.string() ?: "{}")
                    val signal = json.getString("signal")
                    val msg    = json.getString("message")
                    runOnUiThread {
                        comprehensionSignal.visibility = View.VISIBLE
                        comprehensionSignal.text = when (signal) {
                            "green"  -> "🟢 $msg"
                            "yellow" -> "🟡 $msg"
                            else     -> "🔴 $msg"
                        }
                        comprehensionSignal.setBackgroundColor(
                            resources.getColor(when (signal) {
                                "green"  -> android.R.color.holo_green_dark
                                "yellow" -> android.R.color.holo_orange_dark
                                else     -> android.R.color.holo_red_dark
                            }, null))
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { statusText.text = "❌ Error submitting response" }
            }
        }.start()
    }

    private fun fetchSessionSummary() {
        Thread {
            try {
                val body = RequestBody.create(
                    "application/json".toMediaTypeOrNull(),
                    """{"session_id":"$currentSessionId"}""")
                val req = Request.Builder().url("$SERVER/session/summary").post(body).build()
                client.newCall(req).execute().use { resp ->
                    val json = JSONObject(resp.body?.string() ?: "{}")
                    val comp = json.getJSONObject("comprehension")
                    val summary = buildString {
                        appendLine("📋 SESSION SUMMARY")
                        appendLine("Lesson: ${json.getString("lesson_title")}")
                        appendLine("Duration: ${json.getString("duration")}")
                        appendLine("Steps: ${json.getInt("steps_completed")}/${json.getInt("total_steps")}")
                        appendLine("Translations: ${json.getInt("sentences_translated")}")
                        appendLine("Avg latency: ${json.getDouble("avg_translation_latency")}s")
                        appendLine("")
                        appendLine("COMPREHENSION:")
                        appendLine("🟢 Correct: ${comp.getInt("green")}")
                        appendLine("🟡 Partial: ${comp.getInt("yellow")}")
                        appendLine("🔴 Incorrect: ${comp.getInt("red")}")
                        appendLine("Score: ${comp.getInt("score_percent")}%")
                        appendLine(comp.getString("summary"))
                    }
                    runOnUiThread {
                        summaryText.text = summary
                        summaryText.visibility = View.VISIBLE
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { statusText.text = "❌ Error fetching summary" }
            }
        }.start()
    }

    private fun generateWorksheet() {
        runOnUiThread { statusText.text = "⏳ Generating worksheet..." }
        Thread {
            try {
                val body = RequestBody.create(
                    "application/json".toMediaTypeOrNull(),
                    """{"hindi_text":"$lastHindi","santali_text":"$lastSantali",
                       "grade":"2","topic":"Lesson Content",
                       "session_id":"$currentSessionId"}""")
                val req = Request.Builder().url("$SERVER/worksheet").post(body).build()
                client.newCall(req).execute().use { resp ->
                    if (resp.isSuccessful) {
                        val file = File(cacheDir, "worksheet.pdf")
                        file.writeBytes(resp.body?.bytes() ?: byteArrayOf())
                        runOnUiThread {
                            statusText.text = "✅ Worksheet generated (${file.length()/1024}KB)"
                            Toast.makeText(this, "Worksheet ready!", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { statusText.text = "❌ Worksheet error" }
            }
        }.start()
    }

    private fun playAudio(url: String) {
        try {
            val player = MediaPlayer()
            player.setDataSource(url)
            player.prepare()
            player.start()
            player.setOnCompletionListener { it.release() }
        } catch (e: Exception) { /* audio playback failed silently */ }
    }

    private fun writeWav(file: File, samples: ShortArray) {
        val byteRate = SAMPLE_RATE * 2
        file.outputStream().buffered().use { out ->
            fun i4(n: Int) = out.write(byteArrayOf(
                n.and(0xFF).toByte(), n.shr(8).and(0xFF).toByte(),
                n.shr(16).and(0xFF).toByte(), n.shr(24).and(0xFF).toByte()))
            fun i2(n: Int) = out.write(byteArrayOf(
                n.and(0xFF).toByte(), n.shr(8).and(0xFF).toByte()))
            val dataSize = samples.size * 2
            out.write("RIFF".toByteArray()); i4(36 + dataSize)
            out.write("WAVE".toByteArray())
            out.write("fmt ".toByteArray()); i4(16); i2(1)
            i2(1); i4(SAMPLE_RATE); i4(byteRate); i2(2); i2(16)
            out.write("data".toByteArray()); i4(dataSize)
            for (s in samples) i2(s.toInt())
        }
    }
}