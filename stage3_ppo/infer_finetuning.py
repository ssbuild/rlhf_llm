# @Time    : 2023/4/2 22:49
# @Author  : tk
# @FileName: infer_lora_finetuning
import sys
sys.path.append('..')
import re
from collections import OrderedDict
import os
import torch
from deep_training.data_helper import ModelArguments, TrainingArguments, DataArguments
from transformers import HfArgumentParser,AutoConfig,PreTrainedTokenizer

from data_utils import train_info_args, NN_DataHelper
from models import MyPPOTransformer, Generate,LoraArguments,PPOArguments
from config.ppo_config import get_deepspeed_config


deep_config = get_deepspeed_config()


if __name__ == '__main__':
    train_info_args['seed'] = None
    parser = HfArgumentParser((ModelArguments, TrainingArguments, DataArguments, LoraArguments,PPOArguments))
    model_args, _, data_args, _,_ = parser.parse_dict(train_info_args)



    dataHelper = NN_DataHelper(model_args, None, data_args)
    tokenizer, _, _, _ = dataHelper.load_tokenizer_and_config()

    ckpt_dir = './best_ckpt'
    config = AutoConfig.from_pretrained(ckpt_dir)

    pl_model = MyPPOTransformer(config=config, model_args=model_args)
    if deep_config is None:
        train_weight = './best_ckpt/best.pt'
    else:
        # 建议直接使用转换脚本命令 支持 deepspeed stage 0,1,2,3， 生成 ./best_ckpt/last.ckpt/best.pt 权重文件
        # cd best_ckpt/last.ckpt
        # python zero_to_fp32.py . best.pt
        train_weight = './best_ckpt/last.ckpt/best.pt'

    pl_model.load_sft_weight(train_weight)


    pl_model.eval().half().cuda()

    enable_merge_weight = False


    model = pl_model.get_llm_model()

    text = "哪些食物对糖尿病患者有好处?"
    response, history = Generate.chat(model, query=text, tokenizer=tokenizer, max_length=512,
                                      eos_token_id=config.eos_token_id,
                                      do_sample=True, top_p=0.7, temperature=0.95, )
    print('input', text)
    print('output', response)