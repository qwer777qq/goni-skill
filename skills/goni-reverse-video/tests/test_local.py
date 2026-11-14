import importlib.util,json,os,subprocess,tempfile,unittest,shutil,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio',ROOT/'scripts/studio.py')
studio=importlib.util.module_from_spec(spec);spec.loader.exec_module(studio)

class LocalTests(unittest.TestCase):
    def test_presets_and_typewriter_timing(self):
        style=studio.read(ROOT/'assets/owner-review-style.json')
        for name in studio.read(ROOT/'assets/text-presets.json')['presets']:
            result=studio.captions([{'start':1.4,'end':4.2,'text':'제품 확인','preset':name}],style,1.4,5)
            self.assertIn('Dialogue:',result)
        typed=studio.captions([{'start':0,'end':2,'text':'제품','preset':'detail'}],style,1,2)
        events=[x for x in typed.splitlines() if x.startswith('Dialogue:')]
        self.assertEqual(len(events),2)
        self.assertIn('0:00:00.00,0:00:00.05',events[0])
        self.assertIn('0:00:00.05,0:00:02.00',events[1])
        self.assertTrue(events[0].endswith('제'))
        self.assertTrue(events[1].endswith('제품'))
        for invalid in [{'preset':'missing'},{'animation':'missing'},{'color':'red'}]:
            with self.assertRaises(ValueError):studio.captions([{'start':0,'end':2,'text':'제품',**invalid}],style,1,2)
    def test_source_caption_time_and_original_style(self):
        style=studio.read(ROOT/'assets/owner-review-style.json')
        text=studio.captions([{'start':1.4,'end':4.2,'lines':['제품','확인'],'highlight':1}],style,1.4,5)
        self.assertIn('0:00:01.00,0:00:03.00',text)
        self.assertIn('Paperlogy 7 Bold,80',text)
        self.assertIn('\\1c&H009AF5FF&',text)
        self.assertIn('\\t(120,200,\\fscx100',text)
    def test_out_of_range_caption_rejected(self):
        with self.assertRaises(ValueError):studio.captions([{'start':0,'end':8}],studio.read(ROOT/'assets/owner-review-style.json'),1.4,5)
    def test_extreme_pitch_preserving_tempo_chain(self):
        self.assertEqual(studio.tempo(8),'atempo=2,atempo=2,atempo=2')
        self.assertEqual(studio.tempo(.125),'atempo=0.5,atempo=0.5,atempo=0.5')
    def test_no_paid_endpoint(self):
        source=(ROOT/'scripts/studio.py').read_text(encoding='utf-8')
        self.assertNotIn('api.higgsfield.ai',source)
        self.assertNotIn('api-submit',source)
        self.assertNotIn('urlopen',source)
        self.assertNotIn('requests.post',source)
        self.assertNotIn('torch',source)
    def test_length_and_overwrite_preflight(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);m={'clips':[{'path':'source.mp4','in':0,'out':69}], 'output':'out.mp4','speed':1.4,'minimum_duration':50,'fonts_dir':'fonts'}
            studio.write(p/'timeline.json',m)
            info={'format':{'duration':'70'},'streams':[{'codec_type':'video'}]}
            with patch.object(studio,'media',return_value=(info,{'width':1080,'height':1920})):
                with self.assertRaisesRegex(ValueError,'below'):studio.render(p/'timeline.json',True)
                m['clips'][0]['out']=70;(p/'out.mp4').touch();studio.write(p/'timeline.json',m)
                with self.assertRaisesRegex(ValueError,'exists'):studio.render(p/'timeline.json',True)
    def test_user_text_cannot_inject_ass_tags(self):
        self.assertNotIn('\\pos',studio.safe_text('{\\pos(0,0)}'))

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_real_screen_composite_protects_geometry_and_audio(self):
        import cv2
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=288x512:r=24:d=1','-f','lavfi','-i','sine=frequency=440:duration=1','-c:v','libx264','-c:a','aac','-shortest',str(p/'source.mp4')],check=True)
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=lime:s=128x80:r=24:d=1','-c:v','libx264',str(p/'ui.mp4')],check=True)
            m={'source':'source.mp4','screen':'ui.mp4','output':'out.mp4','fixed_camera_confirmed':True,'duration':1,'corners':[[40,100],[248,100],[248,300],[40,300]],'protected_polygons':[[[120,100],[150,100],[150,130],[120,130]]]}
            studio.write(p/'m.json',m);result=studio.screen_compose(p/'m.json')
            cap=cv2.VideoCapture(str(p/'out.mp4'));ok,f=cap.read();cap.release();self.assertTrue(ok)
            self.assertGreater(int(f[200,100,1]),200) # inner screen is green
            self.assertGreater(int(f[110,130,0]),200) # protected original remains blue
            self.assertGreater(int(f[30,30,0]),200) # outside screen unchanged
            self.assertEqual(result['frames'],24)
            self.assertTrue(studio.inspect(p/'out.mp4',True)['audio_present'])
            with self.assertRaisesRegex(ValueError,'exists'):studio.screen_compose(p/'m.json')

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg needed')
    def test_voice_alignment_recovers_known_delay(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);sr=8000;t=np.arange(sr*3)/sr
            env=.2+.15*np.sin(t*5)+.1*np.sin(t*11)
            source=(np.sin(2*np.pi*220*t)*env*28000).astype('<i2')
            for name,a in [('ref',source),('target',np.pad(source,(1600,0)))]:
                with wave.open(str(p/f'{name}.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(a.tobytes())
            studio.write(p/'segments.json',[{'start':.3,'end':2.6}])
            r=studio.align_voice(p/'ref.wav',p/'target.wav',p/'segments.json',p/'align.json')['segments'][0]
            self.assertAlmostEqual(r['shift'],.2,delta=.021)
            self.assertAlmostEqual(r['scale'],1,delta=.005)
            self.assertGreater(r['correlation'],.99)

if __name__=='__main__':unittest.main()
