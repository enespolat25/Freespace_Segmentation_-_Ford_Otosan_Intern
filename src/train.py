
from model1 import FoInternNet
from preprocess import tensorize_image, tensorize_mask, image_mask_check# preprocess dosyası içindeki functionlar import edildi
import os
import glob
import numpy as np
import torch.nn as nn
import torch.optim as optim
import tqdm

######### PARAMETERS ##########
valid_size = 0.3#Validation dataset belirli bir modeli değerlendirmek için kullanılır, ancak bu sık değerlendirme içindir. 
test_size  = 0.1#test edilecek verinin oranı 
batch_size = 4#modelin aynı anda kaç veriyi işleyeceği anlamına gelmektedir.
epochs = 20#Epoch(döngü) sayısı, eğitim sırasında tüm eğitim verilerinin ağa gösterilme sayısıdır.
cuda = False
input_shape = (224, 224)#image hangi boyutta resize edilecek
n_classes = 2
###############################

######### DIRECTORIES #########
SRC_DIR = os.getcwd()#yöntem bize geçerli çalışma dizininin (CWD) konumunu söyler.
ROOT_DIR = os.path.join(SRC_DIR, '..')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
MASK_DIR = os.path.join(DATA_DIR, 'masks')
IMAGE_DIR = os.path.join(DATA_DIR, 'image')
###############################


# PREPARE IMAGE AND MASK LISTS
image_path_list = glob.glob(os.path.join(IMAGE_DIR, '*'))
image_path_list.sort()
#IMAGE_DIR yolundaki dosyaların isimleri listeye alındı ve bunlar sıralandı 
mask_path_list = glob.glob(os.path.join(MASK_DIR, '*'))
mask_path_list.sort()
#MASK_DIR yolundaki dosyaların isimleri listeye eklendi ve bunlar sıralandı

# DATA CHECK
image_mask_check(image_path_list, mask_path_list)
#mask_path_list ve image_path_list listesinde olan elemanların aynı olup olmadığı kontrol edildi



# SHUFFLE INDICES
indices = np.random.permutation(len(image_path_list))
#image_path_list'ın uzunluğu kadar random bir permütasyon dizisi osteps_per_epoch = len(train_input_path_list)//batch_sizeluşturulur 


# DEFINE TEST AND VALID INDICES
test_ind  = int(len(indices) * test_size)#indices uzunluğu ile test_size çarptık ve bunu int şeklinde bir değişkene atadık
valid_ind = int(test_ind + len(indices) * valid_size)

# SLICE TEST DATASET FROM THE WHOLE DATASET
test_input_path_list = image_path_list[:test_ind]#image_path_list listesi'nin  0'dan 476 kadar olan elemanlarını aldık
test_label_path_list = mask_path_list[:test_ind]#mask_path_list listesi'nin  0'dan 476 kadar olan elemanlarını aldık

# SLICE VALID DATASET FROM THE WHOLE DATASET
valid_input_path_list = image_path_list[test_ind:valid_ind]#image_path_list listesi'nin  476'dan 1905'e kadar olan elemanlarını aldık
valid_label_path_list = mask_path_list[test_ind:valid_ind]#mask_path_list listesi'nin  476'dan 1905'e kadar olan elemanlarını aldık

# SLICE TRAIN DATASET FROM THE WHOLE DATASET
train_input_path_list = image_path_list[valid_ind:]#image_path_list listesi'nin 1905'den son elemana kadar olan elemanlarını aldık
train_label_path_list = mask_path_list[valid_ind:]#mask_path_list listesi'nin 1905'den son elemana kadar olan elemanlarını aldık
#burada yukarıda vermiş olduğumuz test verisi için tüm datanın 0.1 ve validation verisi tüm datanın 0.3 içermeli
#ama ikiside aynı data verilerine ait olmaması için datamızı bu şekilde oranlarda böldük


# DEFINE STEPS PER EPOCH
#Tüm veri setinin sinir ağları boyunca bir kere gidip gelmesine(ağırlıkların güncellenmesi) epoch denir.
steps_per_epoch = len(train_input_path_list)//batch_size
# train verisinin(eğitim verisinin) uzunluğunu batch_size bölerek kaç kere  yapılacağı bulunur
#bir epoch içerisinde ,veri seti içerisindeki bir veri dizisi sinir ağlarında sona kadar gider
#daha sonra orada bekler batch size kadar veri sona ulaştıktan sonra hata oranı hesaplanır
#bizim batch_size 4 olduğu için eğitim veri setini//4 e böldük

# CALL MODEL
model = FoInternNet(input_size=input_shape, n_classes=2)
#model'e parametreleri girilip çıktısı değişkene atandı 

# DEFINE LOSS FUNCTION AND OPTIMIZER
criterion = nn.BCELoss()#Hedef ve çıktı arasındaki İkili Çapraz Entropiyi ölçen bir kriter oluşturur:
#BCELoss, yalnızca iki kategorili problem için kullanılan BCOMoss CrossEntropyLoss'un özel bir durumu olan Binary CrossEntropyLoss'un kısaltmasıdır
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
#Genelde kullanılan momentum beta katsayısı 0.9'dur.
#lr=learning rate

# IF CUDA IS USED, IMPORT THE MODEL INTO CUDA
if cuda:
    model = model.cuda()


# TRAINING THE NEURAL NETWORK
for epoch in tqdm.tqdm(range(epochs)):
    running_loss = 0
    for ind in range(steps_per_epoch):
        batch_input_path_list = test_input_path_list[batch_size*ind:batch_size*(ind+1)]
        batch_label_path_list = test_label_path_list[batch_size*ind:batch_size*(ind+1)]
        batch_input = tensorize_image(batch_input_path_list, input_shape, cuda)#fonksiyonlar parametreleri girilerek değişkene atandı 
        batch_label = tensorize_mask(batch_label_path_list, input_shape, n_classes, cuda)
        
        optimizer.zero_grad()#gradyanı sıfırlar yoksa her yinelemede birikme oluşur

        outputs = model(batch_input) # modele batch_inputu parametre olarak verip oluşan çıktıyı değişkene atadık 

        # Forward passes the input data
        loss = criterion(outputs, batch_label)#hedef ve çıktı arasındaki ikili çapraz entropiyi ölçer 
        loss.backward()# Gradyanı hesaplar, her bir parametrenin ne kadar güncellenmesi gerektiğini verir
        optimizer.step()# Gradyana göre her parametreyi günceller

        running_loss += loss.item()
        print(ind)
        if ind == steps_per_epoch-1:
            print('training loss on epoch {}: {}'.format(epoch, running_loss))
            val_loss = 0
            for (valid_input_path, valid_label_path) in zip(valid_input_path_list, valid_label_path_list):
                batch_input = tensorize_image([valid_input_path], input_shape, cuda)
                batch_label = tensorize_mask([valid_label_path], input_shape, n_classes, cuda)
                outputs = model(batch_input)
                loss = criterion(outputs, batch_label)
                val_loss += loss
                break

            print('validation loss on epoch {}: {}'.format(epoch, val_loss))
# zip:
#letters = ['a', 'b', 'c']
#numbers = [0, 1, 2]
#for l, n in zip(letters, numbers):
    #print(f'Letter: {l}')
    #print(f'Number: {n}')
# Letter: a
# Number: 0
# Letter: b
# Number: 1
# Letter: c
# Number: 2