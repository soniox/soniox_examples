import fs from 'fs';
import process from 'process';
import { parseArgs } from 'node:util';
import { SonioxNodeClient } from '@soniox/node';

// Initialize the client.
// The API key is read from the SONIOX_API_KEY environment variable.
const client = new SonioxNodeClient();

// Convert transcript into a readable output.
function renderTranscript(transcript) {
  return transcript
    .segments()
    .map((s) => {
      const speaker = s.speaker ? `Speaker ${s.speaker}` : '';
      const isTranslation = s.tokens[0]?.translation_status === 'translation';
      const lang = isTranslation ? `[Translation][${s.language}]` : `[${s.language}]`;
      return `${speaker} ${lang}: ${s.text.trim()}`;
    })
    .join('\n');
}

// Build transcription options.
function getTranscriptionOptions(audioUrl, audioPath, translation) {
  if (!audioUrl && !audioPath) {
    throw new Error('Missing audio: audio_url or audio_path must be specified.');
  }

  const options = {
    // Select the model to use.
    // See: soniox.com/docs/stt/models
    model: 'stt-async-v4',

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

    // Optional identifier to track this request (client-defined).
    client_reference_id: 'MyReferenceId',

    // Wait for transcription to complete and fetch the transcript.
    wait: true,

    // Automatically clean up the file and transcription after we're done.
    cleanup: ['file', 'transcription'],
  };

  // Audio source: either a local file or a public URL.
  if (audioPath) {
    options.file = fs.readFileSync(audioPath);
    options.filename = audioPath;
  } else {
    options.audio_url = audioUrl;
  }

  // Translation options.
  // See: soniox.com/docs/stt/rt/real-time-translation#translation-modes
  if (translation === 'one_way') {
    options.translation = { type: 'one_way', target_language: 'es' };
  } else if (translation === 'two_way') {
    options.translation = {
      type: 'two_way',
      language_a: 'en',
      language_b: 'es',
    };
  } else if (translation !== 'none') {
    throw new Error(`Unsupported translation: ${translation}`);
  }

  return options;
}

async function transcribeFile(audioUrl, audioPath, translation) {
  console.log('Starting transcription...');
  const transcription = await client.stt.transcribe(getTranscriptionOptions(audioUrl, audioPath, translation));
  console.log(renderTranscript(transcription.transcript));
}

async function deleteAllFiles() {
  const { deleted } = await client.files.purge();
  console.log(deleted === 0 ? 'No files to delete.' : `Deleted ${deleted} files.`);
}

async function deleteAllTranscriptions() {
  const { deleted } = await client.stt.purge();
  console.log(deleted === 0 ? 'No transcriptions to delete.' : `Deleted ${deleted} transcriptions.`);
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      audio_url: {
        type: 'string',
        description: 'Public URL of the audio file to transcribe',
      },
      audio_path: {
        type: 'string',
        description: 'Path to a local audio file to transcribe',
      },
      delete_all_files: {
        type: 'boolean',
        description: 'Delete all uploaded files',
      },
      delete_all_transcriptions: {
        type: 'boolean',
        description: 'Delete all transcriptions',
      },
      translation: { type: 'string', default: 'none' },
    },
  });

  if (argv.delete_all_files) {
    await deleteAllFiles();
    return;
  }

  if (argv.delete_all_transcriptions) {
    await deleteAllTranscriptions();
    return;
  }

  await transcribeFile(argv.audio_url, argv.audio_path, argv.translation);
}

main().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
