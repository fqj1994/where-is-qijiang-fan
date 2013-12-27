package me.fqj.android.locationupdater;

import android.content.SharedPreferences;
import android.os.AsyncTask;
import android.os.Bundle;
import android.app.Activity;
import android.util.Log;
import android.view.Menu;
import android.widget.EditText;
import android.widget.TextView;
import android.view.View;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationProvider;
import android.location.LocationManager;
import android.content.Context;
import android.os.Looper;

import com.google.android.gms.gcm.GoogleCloudMessaging;

import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;

import java.io.IOException;
import java.util.Calendar;

public class MainActivity extends Activity {

    private String SENDER_ID = "";
    private String REGID_REPORT= "";
    private String regid = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        SharedPreferences pref = getPreferences(MODE_PRIVATE);
        ((EditText)findViewById(R.id.editText)).setText(pref.getString("me.fqj.android.locationupdater.sender_id", ""));
        ((EditText)findViewById(R.id.editText2)).setText(pref.getString("me.fqj.android.locationupdater.locreport", ""));
        ((EditText)findViewById(R.id.editText3)).setText(pref.getString("me.fqj.android.locationupdater.regidreport", ""));
        SENDER_ID = pref.getString("me.fqj.android.locationupdater.sender_id", "");
        REGID_REPORT = pref.getString("me.fqj.android.locationupdater.regidreport", "");
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        //getMenuInflater().inflate(R.menu.main, menu);
        return true;
    }

    public void onSaveButtonClicked(View view) {
        SharedPreferences pref = getPreferences(MODE_PRIVATE);
        SharedPreferences.Editor editor = pref.edit();
        editor.putString("me.fqj.android.locationupdater.sender_id", ((EditText)findViewById(R.id.editText)).getText().toString());
        editor.putString("me.fqj.android.locationupdater.locreport", ((EditText)findViewById(R.id.editText2)).getText().toString());
        editor.putString("me.fqj.android.locationupdater.regidreport", ((EditText)findViewById(R.id.editText3)).getText().toString());
        SENDER_ID = ((EditText)findViewById(R.id.editText)).getText().toString();
        REGID_REPORT = ((EditText)findViewById(R.id.editText3)).getText().toString();
        editor.commit();
        Log.d("LocationUpdater", "saved conf");
    }

    public void onStartButtonClicked(View view) {
        onSaveButtonClicked(view);
        ((TextView)findViewById(R.id.textView3)).setText("Starting");
        new AsyncTask() {
            @Override
            protected String doInBackground(Object... params) {
                String msg;
                GoogleCloudMessaging gcm = GoogleCloudMessaging.getInstance(getApplicationContext());
                try {
                    regid = gcm.register(SENDER_ID);
                    new DefaultHttpClient().execute(new HttpGet(REGID_REPORT + regid));
                    Log.d("LocationUpdater", "start success");
                    msg = "Start Success";
                } catch (IOException ex) {
                    msg = ("Start Failure, " + ex.toString());
                    Log.d("LocationUpdater", "start error");
                }
                return msg;
            }
            @Override
            protected void onPostExecute(Object msg) {
                ((TextView)findViewById(R.id.textView3)).setText((String)msg);
            }
        }.execute(null, null, null);
    }

    public void onStopButtonClicked(View view) {
        ((TextView)findViewById(R.id.textView3)).setText("Stopping");
        new AsyncTask() {
            @Override
            protected String doInBackground(Object... params) {
                GoogleCloudMessaging gcm = GoogleCloudMessaging.getInstance(getApplicationContext());
                String msg = "Stopped";
                try {
                    gcm.unregister();
                    new DefaultHttpClient().execute(new HttpGet(REGID_REPORT));
                } catch (IOException ex) {
                    msg = ex.toString();
                }
                return msg;
            }
            @Override
            protected void onPostExecute(Object msg) {
                ((TextView)findViewById(R.id.textView3)).setText((String)msg);
            }
        }.execute(null, null, null);
    }
}
