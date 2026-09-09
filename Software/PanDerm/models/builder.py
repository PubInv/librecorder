import timm
from .timm_wrapper import TimmCNNEncoder
import torch
from torch import nn
from torchvision import transforms
from models.modeling_finetune import *
import open_clip

from models.modeling_finetune import VisionTransformer
from utils.utils import cae_kwargs
from functools import partial

def get_norm_constants(which_img_norm: str = 'imagenet'):
    print('normalization method: ',which_img_norm)
    constants_zoo = {
        'imagenet': {'mean': (0.485, 0.456, 0.406), 'std': (0.228, 0.224, 0.225)},
        'openai_clip':{'mean': (0.48145466, 0.4578275, 0.40821073), 'std': (0.26862954, 0.26130258, 0.27577711)},
        'uniform': {'mean': (0.5, 0.5, 0.5), 'std': (0.5, 0.5, 0.5)}
    }

    constants = constants_zoo[which_img_norm]
    return constants.get('mean'), constants.get('std')

def get_eval_transforms(
        which_img_norm: str = 'imagenet',
        img_resize: int = 224,
        center_crop: bool = False
):
    r"""
    Gets the image transformation for normalizing images before feature extraction.

    Args:
        - which_img_norm (str): transformation type

    Return:
        - eval_transform (torchvision.Transform): PyTorch transformation function for images.
    """
    mean, std = get_norm_constants(which_img_norm)
    eval_trans = [transforms.Resize(256),
                 transforms.CenterCrop(224),
                 transforms.ToTensor(),
                 transforms.Normalize(mean=mean, std=std)]
    eval_transform = transforms.Compose(eval_trans)
    return eval_transform


def get_encoder(args, model_name,which_img_norm='imagenet'):
    # which_img_norm='imagenet'
    print('loading model checkpoint')

    if model_name == 'imgnet_large21k':
        model = timm.create_model(args.pretrained_checkpoint,
                                  num_classes=0,
                                  dynamic_img_size=True,
                                  pretrained=True)
    elif model_name == 'SwAVDerm':
        model = TimmCNNEncoder(kwargs = {'features_only': True, 'out_indices': (4,), 'pretrained': True, 'num_classes': 0})
        checkpoint = torch.load(args.pretrained_checkpoint, map_location='cpu')
        state_dict = checkpoint['state_dict']
        state_dict = {k.replace('module', 'model'): v for k, v in state_dict.items()}
        model.load_state_dict(state_dict, strict=False)
    elif model_name == 'dinov2':
        model = timm.create_model("vit_large_patch14_dinov2.lvd142m",
                                  num_classes=0,
                                  dynamic_img_size=True,
                                  pretrained=True)
    elif model_name == 'PanDerm_Large_LP':
        model = panderm_large_patch16_224()
        state_dict = torch.load(args.pretrained_checkpoint, map_location='cpu',weights_only=True)
        state_dict = {k.replace("encoder.", ""): v for k, v in state_dict.items()}
        model.load_state_dict(state_dict, strict=False)
    elif model_name == 'PanDerm_Base_LP':
        model = panderm_base_patch16_224()

        model.load_state_dict(torch.load(args.pretrained_checkpoint, map_location='cpu'), strict=False) 
        model.head = torch.nn.Identity()
    else:
        raise NotImplementedError('model {} not implemented'.format(model_name))
    
    print(model)
    # constants = MODEL2CONSTANTS[model_name]
    eval_transform = get_eval_transforms(
        which_img_norm=which_img_norm,
        img_resize=256,
        center_crop=True
    )
    # img_transforms = get_eval_transforms(mean=constants['mean'],
    #                                      std=constants['std'],
    #                                      target_img_size = target_img_size)

    return model, eval_transform