import fs from 'fs';
import process from 'process';
import { parseArgs } from 'node:util';
import { SonioxNodeClient, RealtimeUtteranceBuffer } from '@soniox/node';

// Initialize the client.
// The API key is read from the SONIOX_API_KEY environment variable.
const client = new SonioxNodeClient();

// Get session config based on CLI arguments.
function getSessionConfig(audioFormat, translation) {
  const config = {
    // Select the model to use.
    // See: soniox.com/docs/stt/models
    model: 'stt-rt-v4',

    // Set language hints when possible to significantly improve accuracy.
    // See: soniox.com/docs/stt/concepts/language-hints
    language_hints: ['en', 'es'],

    // Enable language identification. Each token will include a "language" field.
    // See: soniox.com/docs/stt/concepts/language-identification
    enable_language_identification: true,

    // Enable speaker diarization. Each token will include a "speaker" field.
    // See: soniox.com/docs/stt/concepts/speaker-diarization
    enable_speaker_diarization: true,

    // Set context to help the model understand your domain, recognize important terms,
    // and apply custom vocabulary and translation preferences.
    // See: soniox.com/docs/stt/concepts/context
    context: {
      general: [
        { key: 'domain', value: 'Healthcare' },
        { key: 'topic', value: 'Diabetes management consultation' },
        { key: 'doctor', value: 'Dr. Martha Smith' },
        { key: 'patient', value: 'Mr. David Miller' },
        { key: 'organization', value: "St John's Hospital" },
      ],
      text: 'Mr. David Miller visited his healthcare provider last month for a routine follow-up related to diabetes care. The clinician reviewed his recent test results, noted improved glucose levels, and adjusted his medication schedule accordingly. They also discussed meal planning strategies and scheduled the next check-up for early spring.',
      terms: ['Celebrex', 'Zyrtec', 'Xanax', 'Prilosec', 'Amoxicillin Clavulanate Potassium'],
      translation_terms: [
        { source: 'Mr. Smith', target: 'Sr. Smith' },
        { source: "St John's", target: "St John's" },
        { source: 'stroke', target: 'ictus' },
      ],
    },

    // Use endpointing to detect when the speaker stops.
    // It finalizes all non-final tokens right away, minimizing latency.
    // See: soniox.com/docs/stt/rt/endpoint-detection
    enable_endpoint_detection: true,
  };

  // Audio format.
  // See: soniox.com/docs/stt/rt/real-time-transcription#audio-formats
  if (audioFormat === 'auto') {
    config.audio_format = 'auto';
  } else if (audioFormat === 'pcm_s16le') {
    config.audio_format = 'pcm_s16le';
    config.sample_rate = 16000;
    config.num_channels = 1;
  } else {
    throw new Error(`Unsupported audio_format: ${audioFormat}`);
  }

  // Translation options.
  // See: soniox.com/docs/stt/rt/real-time-translation#translation-modes
  if (translation === 'one_way') {
    config.translation = { type: 'one_way', target_language: 'es' };
  } else if (translation === 'two_way') {
    config.translation = {
      type: 'two_way',
      language_a: 'en',
      language_b: 'es',
    };
  } else if (translation !== 'none') {
    throw new Error(`Unsupported translation: ${translation}`);
  }

  return config;
}

// Render a single utterance as readable text.
function renderUtterance(utterance) {
  return utterance.segments
    .map((segment) => {
      const speaker = segment.speaker ? `Speaker ${segment.speaker}:` : '';
      const isTranslation = segment.tokens[0]?.translation_status === 'translation';
      const lang = segment.language ? `${isTranslation ? '[Translation] ' : ''}[${segment.language}]` : '';
      return `${speaker} ${lang} ${segment.text.trimStart()}`;
    })
    .join('\n');
}

async function runSession(audioPath, audioFormat, translation) {
  const config = getSessionConfig(audioFormat, translation);

  // Create a real-time STT session.
  const session = client.realtime.stt(config);

  // Utterance buffer collects tokens and flushes complete utterances on endpoints.
  const buffer = new RealtimeUtteranceBuffer();

  // Feed every result into the buffer.
  session.on('result', (result) => {
    buffer.addResult(result);
  });

  // When an endpoint is detected, flush the buffer into a complete utterance.
  session.on('endpoint', () => {
    const utterance = buffer.markEndpoint();
    if (utterance) {
      console.log(renderUtterance(utterance));
    }
  });

  session.on('finished', () => {
    // Flush any remaining tokens after the session ends.
    const utterance = buffer.markEndpoint();
    if (utterance) {
      console.log(renderUtterance(utterance));
    }
    console.log('Session finished.');
  });

  session.on('error', (err) => {
    console.error('Session error:', err);
  });

  // Connect to the Soniox realtime API.
  console.log('Connecting to Soniox...');
  await session.connect();
  console.log('Session started.');

  // Stream the audio file and finish when done.
  await session.sendStream(fs.createReadStream(audioPath, { highWaterMark: 3840 }), { pace_ms: 120, finish: true });
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      audio_path: { type: 'string' },
      audio_format: { type: 'string', default: 'auto' },
      translation: { type: 'string', default: 'none' },
    },
  });

  if (!argv.audio_path) {
    throw new Error('Missing --audio_path argument.');
  }

  await runSession(argv.audio_path, argv.audio_format, argv.translation);
}

main().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
