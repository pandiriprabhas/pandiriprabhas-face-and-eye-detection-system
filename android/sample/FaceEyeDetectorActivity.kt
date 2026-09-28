// Sample Activity file for reference only. Integrate into your Android Studio project.
package com.example.faceeye

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.SurfaceView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import org.opencv.android.*
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import org.opencv.objdetect.CascadeClassifier
import java.io.File
import java.io.FileOutputStream

class FaceEyeDetectorActivity : AppCompatActivity(), CameraBridgeViewBase.CvCameraViewListener2 {
    private lateinit var cameraView: JavaCameraView
    private var faceCascade: CascadeClassifier? = null
    private var eyeCascade: CascadeClassifier? = null

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> if (granted) cameraView.enableView() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        cameraView = JavaCameraView(this, -1)
        setContentView(cameraView)
        cameraView.visibility = SurfaceView.VISIBLE
        cameraView.setCvCameraViewListener(this)

        if (!OpenCVLoader.initDebug()) {
            OpenCVLoader.initAsync(OpenCVLoader.OPENCV_VERSION, this, object : BaseLoaderCallback(this) {
                override fun onManagerConnected(status: Int) {
                    if (status == SUCCESS) initDetectorsAndStart() else super.onManagerConnected(status)
                }
            })
        } else {
            initDetectorsAndStart()
        }
    }

    private fun initDetectorsAndStart() {
        faceCascade = loadCascadeFromRaw(R.raw.haarcascade_frontalface_default)
        eyeCascade = loadCascadeFromRaw(R.raw.haarcascade_eye)
        val has = ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
        if (has) cameraView.enableView() else permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    private fun loadCascadeFromRaw(id: Int): CascadeClassifier? {
        val input = resources.openRawResource(id)
        val cascadeDir = getDir("cascades", MODE_PRIVATE)
        val cascadeFile = File(cascadeDir, "$id.xml")
        FileOutputStream(cascadeFile).use { output -> input.copyTo(output) }
        val classifier = CascadeClassifier(cascadeFile.absolutePath)
        if (classifier.empty()) return null
        cascadeDir.delete()
        return classifier
    }

    override fun onCameraViewStarted(width: Int, height: Int) {}
    override fun onCameraViewStopped() {}

    override fun onCameraFrame(inputFrame: CameraBridgeViewBase.CvCameraViewFrame): Mat {
        val rgba = inputFrame.rgba()
        val gray = inputFrame.gray()
        Imgproc.equalizeHist(gray, gray)
        val faces = MatOfRect()
        faceCascade?.detectMultiScale(gray, faces, 1.1, 5, 0, Size(80.0, 80.0), Size())
        for (r in faces.toArray()) {
            Imgproc.rectangle(rgba, r, Scalar(0.0, 255.0, 0.0, 255.0), 3)
            val roiGray = gray.submat(r)
            val roiRect = MatOfRect()
            eyeCascade?.detectMultiScale(roiGray, roiRect, 1.1, 3)
            for (e in roiRect.toArray()) {
                val eye = Rect(r.x + e.x, r.y + e.y, e.width, e.height)
                Imgproc.rectangle(rgba, eye, Scalar(255.0, 0.0, 0.0, 255.0), 2)
            }
            roiGray.release()
        }
        faces.release()
        return rgba
    }

    override fun onPause() { super.onPause(); cameraView.disableView() }
    override fun onDestroy() { super.onDestroy(); cameraView.disableView() }
}
