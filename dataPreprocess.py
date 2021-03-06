import pretty_midi as pm
import pandas as pd
import numpy as np
import os
from functools import reduce
import operator
from sklearn.decomposition import PCA


# Pitch from C-1 to G-9 values 0-127
# velocity - indicates volume level, 1-127 as well

Normalized_Pitch = 127
data_path = 'C:/code/course/Deep_learning/Ass3/Data'


def music_to_csv(midi_files_path):
    '''
    :param midi_files_path: the path where all the midi files are stored
    :return: creates a folder under data_path named song representations and outputs
             some files to represent each song, doesnt return anything.
    '''
    tick_window = 100
    try:
        os.mkdir(os.path.join(data_path, "song_representations"))
    except FileExistsError:
        pass

    for song_path in os.listdir(midi_files_path):
        try:
            midi_file = pm.PrettyMIDI(os.path.join(midi_files_path, song_path))
            song_encoding = []
            for time in range(0, len(midi_file._PrettyMIDI__tick_to_time), tick_window):
                time_stamp = []
                start_time = midi_file.tick_to_time(time)
                end_time = midi_file.tick_to_time(time + tick_window)
                time_stamp.append(start_time)
                time_stamp.append(end_time)
                time_stamp.append(get_key_sig(midi_file.key_signature_changes, start_time))
                time_stamp.append(get_time_sig(midi_file.time_signature_changes, start_time))
                for instrument in midi_file.instruments:
                    time_stamp += get_instrument_info(instrument, start_time, end_time)
                song_encoding.append(time_stamp)

            gooal_columns = ['start_time',
                             'end_time',
                             'key_signature',
                             'time_signature'
                             ]

            for idx, instrument in enumerate(midi_file.instruments):
                for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']:
                    gooal_columns.append(f'instrument {str(idx)}: {note}')
                gooal_columns.append(f'instrument {str(idx)}: velocity')

            df = pd.DataFrame(song_encoding,
                              columns=gooal_columns)
            df.to_csv(os.path.join(data_path, "song_representations/", song_path+'.csv'), sep='\t', index=False)
        except Exception as e:
            print(e)


def create_pca_to_csv(songs_folder: str):
    # pca size, other sizes where problemetic, can be altered
    pca_comp_amount = 30
    songs_names = list()
    final_pcas = list()
    for song_path in os.listdir(songs_folder):
        df = pd.read_csv(os.path.join(songs_folder, song_path), sep='\t')
        songs_names.append([song_path])
        pca = PCA(n_components=min(pca_comp_amount, df.shape[1]))
        pca.fit(df.to_numpy(dtype="float"))
        res = np.zeros((pca_comp_amount, 200))
        pca_comps = pca.components_
        res[:pca_comps.shape[0], : pca_comps.shape[1]] = pca_comps[:, :200]
        res = res.reshape((1, pca_comp_amount*200))
        final_pcas.append(res[0])

    final_np = np.concatenate((songs_names, final_pcas), axis=1)
    pd.DataFrame(final_np).to_csv(os.path.join(data_path, "pcas.csv"), index=False)


def get_key_sig(key_signatures, start_time):
    for key_sig in key_signatures:
        if start_time >= key_sig.time:
            return key_sig.key_number
    return 0


def get_time_sig(time_signatures, start_time):
    for time_sig in time_signatures:
        if start_time >= time_sig.time:
            return time_sig.numerator / time_sig.denominator
    return 0


def collect_relvant_notes(instrument, start_time, end_time):
    relevant_notes = []
    for curr_note in instrument.notes:
        if curr_note.start < start_time:
            continue
        if curr_note.end >= end_time:
            break
        relevant_notes.append(curr_note)
    return relevant_notes


def get_instrument_info(instrument, start_time, end_time):
    notes = collect_relvant_notes(instrument, start_time, end_time)
    ans = [0] * 13
    if len(notes) == 0:
        return ans
    ans[-1] = reduce(operator.add, map(lambda note: note.velocity, notes)) / len(notes)
    for note in notes:
        ans[note.pitch % 12] = 1
    return ans


def main():
    # data path is defined in the beginning of the file,
    # we expect every other data folder to be under it/data file
    midi_dir = 'midi_files'
    # music to csv takes each song and make a represntative of it
    music_to_csv(os.path.join(data_path, midi_dir))
    # following that we make a PCA dimension reduction for each input, and export as csv under data path
    create_pca_to_csv(os.path.join(data_path, midi_dir))


if __name__ == '__main__':
    main()
